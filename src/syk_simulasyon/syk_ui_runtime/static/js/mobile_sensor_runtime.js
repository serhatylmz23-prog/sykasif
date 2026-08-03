(() => {
    "use strict";

    const API =
        "/api/syk-ui/mobile-sensors";

    const state = {
        cameraStream: null,
        microphoneStream: null,
        locationWatchId: null,
        cameraFacingMode:
            "environment",
        videoElement: null,
        canvasElement: null,
    };

    async function fetchJson(
        url,
        options = {}
    ) {
        const response = await fetch(
            url,
            {
                headers: {
                    "Content-Type":
                        "application/json",
                    Accept:
                        "application/json",
                    ...(options.headers || {}),
                },
                ...options,
            }
        );

        let payload = {};

        try {
            payload =
                await response.json();
        }
        catch {
        }

        if (!response.ok) {
            throw new Error(
                payload.detail
                || "Sensör işlemi başarısız."
            );
        }

        return payload;
    }

    async function updatePermission(
        sensorType,
        permissionState
    ) {
        return fetchJson(
            `${API}/permissions`,
            {
                method: "PATCH",
                body: JSON.stringify({
                    sensor_type:
                        sensorType,
                    state:
                        permissionState,
                }),
            }
        );
    }

    function ensureCameraElements() {
        let video =
            document.querySelector(
                "#syk-mobile-camera-video"
            );

        let canvas =
            document.querySelector(
                "#syk-mobile-camera-canvas"
            );

        if (!video) {
            video =
                document.createElement(
                    "video"
                );

            video.id =
                "syk-mobile-camera-video";

            video.autoplay = true;
            video.muted = true;
            video.playsInline = true;
            video.hidden = true;

            document.body.appendChild(
                video
            );
        }

        if (!canvas) {
            canvas =
                document.createElement(
                    "canvas"
                );

            canvas.id =
                "syk-mobile-camera-canvas";

            canvas.hidden = true;

            document.body.appendChild(
                canvas
            );
        }

        state.videoElement = video;
        state.canvasElement = canvas;

        return {
            video,
            canvas,
        };
    }

    async function startCamera(
        options = {}
    ) {
        if (
            !navigator.mediaDevices
            || !navigator.mediaDevices
                .getUserMedia
        ) {
            await updatePermission(
                "camera",
                "unsupported"
            );

            throw new Error(
                "Kamera bu tarayıcıda " +
                "desteklenmiyor."
            );
        }

        await stopCamera();

        const facingMode =
            options.facingMode
            || state.cameraFacingMode;

        try {
            const stream =
                await navigator
                    .mediaDevices
                    .getUserMedia(
                        {
                            video: {
                                facingMode: {
                                    ideal:
                                        facingMode,
                                },
                                width: {
                                    ideal:
                                        options.width
                                        || 1280,
                                },
                                height: {
                                    ideal:
                                        options.height
                                        || 720,
                                },
                                frameRate: {
                                    ideal:
                                        options.frameRate
                                        || 24,
                                },
                            },
                            audio: false,
                        }
                    );

            await updatePermission(
                "camera",
                "granted"
            );

            const {
                video,
            } = ensureCameraElements();

            video.srcObject = stream;

            await video.play();

            const track =
                stream.getVideoTracks()[0];

            const settings =
                track.getSettings();

            state.cameraStream = stream;

            state.cameraFacingMode =
                settings.facingMode
                || facingMode;

            const result =
                await fetchJson(
                    `${API}/camera/start`,
                    {
                        method: "POST",
                        body: JSON.stringify({
                            facing_mode:
                                state
                                    .cameraFacingMode,
                            width:
                                settings.width
                                || video.videoWidth
                                || 1280,
                            height:
                                settings.height
                                || video.videoHeight
                                || 720,
                            frame_rate:
                                settings.frameRate
                                || 24,
                            stream_id:
                                track.id,
                        }),
                    }
                );

            document.dispatchEvent(
                new CustomEvent(
                    "syk:camera-started",
                    {
                        detail: result,
                    }
                )
            );

            return result;
        }
        catch (error) {
            await updatePermission(
                "camera",
                (
                    error.name
                    === "NotAllowedError"
                        ? "denied"
                        : "prompt"
                )
            );

            throw error;
        }
    }

    async function stopCamera() {
        if (state.cameraStream) {
            for (
                const track
                of state.cameraStream
                    .getTracks()
            ) {
                track.stop();
            }

            state.cameraStream = null;
        }

        if (state.videoElement) {
            state.videoElement
                .srcObject = null;
        }

        const result =
            await fetchJson(
                `${API}/camera/stop`,
                {
                    method: "POST",
                }
            ).catch(
                () => null
            );

        document.dispatchEvent(
            new CustomEvent(
                "syk:camera-stopped",
                {
                    detail: result,
                }
            )
        );

        return result;
    }

    async function captureFrame(
        options = {}
    ) {
        if (
            !state.cameraStream
            || !state.videoElement
        ) {
            throw new Error(
                "Kamera açık değil."
            );
        }

        const {
            video,
            canvas,
        } = ensureCameraElements();

        const width =
            options.width
            || video.videoWidth;

        const height =
            options.height
            || video.videoHeight;

        if (!width || !height) {
            throw new Error(
                "Kamera görüntü ölçüsü " +
                "alınamadı."
            );
        }

        canvas.width = width;
        canvas.height = height;

        const context =
            canvas.getContext(
                "2d",
                {
                    alpha: false,
                }
            );

        context.drawImage(
            video,
            0,
            0,
            width,
            height
        );

        const mimeType =
            options.mimeType
            || "image/jpeg";

        const quality =
            options.quality
            ?? 0.88;

        const blob =
            await new Promise(
                (resolve, reject) => {
                    canvas.toBlob(
                        value => {
                            if (value) {
                                resolve(value);
                            }
                            else {
                                reject(
                                    new Error(
                                        "Kamera karesi "
                                        + "üretilemedi."
                                    )
                                );
                            }
                        },
                        mimeType,
                        quality
                    );
                }
            );

        const dataBase64 =
            await blobToBase64(
                blob
            );

        const deviceId =
            window.SyKMobileRuntime
                ?.snapshot()
                ?.deviceId
            || "SYK-BROWSER-UNKNOWN";

        const result =
            await fetchJson(
                `${API}/frames`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        device_id:
                            deviceId,
                        data_base64:
                            dataBase64,
                        mime_type:
                            mimeType,
                        width,
                        height,
                        source:
                            "browser_camera",
                    }),
                }
            );

        document.dispatchEvent(
            new CustomEvent(
                "syk:mobile-frame-captured",
                {
                    detail: result,
                }
            )
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:media-analysis-requested",
                {
                    detail: {
                        frame: result,
                        blob,
                    },
                }
            )
        );

        return {
            record: result,
            blob,
        };
    }

    async function startMicrophone(
        options = {}
    ) {
        if (
            !navigator.mediaDevices
            || !navigator.mediaDevices
                .getUserMedia
        ) {
            await updatePermission(
                "microphone",
                "unsupported"
            );

            throw new Error(
                "Mikrofon bu tarayıcıda " +
                "desteklenmiyor."
            );
        }

        await stopMicrophone();

        try {
            const stream =
                await navigator
                    .mediaDevices
                    .getUserMedia(
                        {
                            audio: {
                                channelCount: {
                                    ideal:
                                        options.channels
                                        || 1,
                                },
                                sampleRate: {
                                    ideal:
                                        options.sampleRate
                                        || 16000,
                                },
                                echoCancellation:
                                    true,
                                noiseSuppression:
                                    true,
                                autoGainControl:
                                    true,
                            },
                            video: false,
                        }
                    );

            await updatePermission(
                "microphone",
                "granted"
            );

            const track =
                stream.getAudioTracks()[0];

            const settings =
                track.getSettings();

            state.microphoneStream =
                stream;

            const result =
                await fetchJson(
                    `${API}/microphone/start`,
                    {
                        method: "POST",
                        body: JSON.stringify({
                            sample_rate:
                                settings.sampleRate
                                || options.sampleRate
                                || 16000,
                            channels:
                                settings.channelCount
                                || options.channels
                                || 1,
                            stream_id:
                                track.id,
                        }),
                    }
                );

            document.dispatchEvent(
                new CustomEvent(
                    "syk:microphone-started",
                    {
                        detail: result,
                    }
                )
            );

            document.dispatchEvent(
                new CustomEvent(
                    "syk:jarmin-microphone-ready",
                    {
                        detail: {
                            stream,
                            settings:
                                result,
                        },
                    }
                )
            );

            return result;
        }
        catch (error) {
            await updatePermission(
                "microphone",
                (
                    error.name
                    === "NotAllowedError"
                        ? "denied"
                        : "prompt"
                )
            );

            throw error;
        }
    }

    async function stopMicrophone() {
        if (state.microphoneStream) {
            for (
                const track
                of state.microphoneStream
                    .getTracks()
            ) {
                track.stop();
            }

            state.microphoneStream =
                null;
        }

        const result =
            await fetchJson(
                `${API}/microphone/stop`,
                {
                    method: "POST",
                }
            ).catch(
                () => null
            );

        document.dispatchEvent(
            new CustomEvent(
                "syk:microphone-stopped",
                {
                    detail: result,
                }
            )
        );

        return result;
    }

    async function requestLocation(
        options = {}
    ) {
        if (
            !("geolocation" in navigator)
        ) {
            await updatePermission(
                "location",
                "unsupported"
            );

            throw new Error(
                "Konum servisi bu cihazda " +
                "desteklenmiyor."
            );
        }

        return new Promise(
            (resolve, reject) => {
                navigator.geolocation
                    .getCurrentPosition(
                        async position => {
                            try {
                                await updatePermission(
                                    "location",
                                    "granted"
                                );

                                const result =
                                    await sendLocation(
                                        position
                                    );

                                resolve(result);
                            }
                            catch (error) {
                                reject(error);
                            }
                        },
                        async error => {
                            await updatePermission(
                                "location",
                                (
                                    error.code === 1
                                        ? "denied"
                                        : "prompt"
                                )
                            );

                            reject(error);
                        },
                        {
                            enableHighAccuracy:
                                options
                                    .enableHighAccuracy
                                ?? true,
                            timeout:
                                options.timeout
                                || 12000,
                            maximumAge:
                                options.maximumAge
                                || 0,
                        }
                    );
            }
        );
    }

    function startLocationWatch(
        options = {}
    ) {
        if (
            !("geolocation" in navigator)
        ) {
            throw new Error(
                "Konum servisi desteklenmiyor."
            );
        }

        stopLocationWatch();

        state.locationWatchId =
            navigator.geolocation
                .watchPosition(
                    position => {
                        updatePermission(
                            "location",
                            "granted"
                        ).catch(
                            () => {}
                        );

                        sendLocation(
                            position
                        ).catch(
                            () => {}
                        );
                    },
                    error => {
                        updatePermission(
                            "location",
                            (
                                error.code === 1
                                    ? "denied"
                                    : "prompt"
                            )
                        ).catch(
                            () => {}
                        );
                    },
                    {
                        enableHighAccuracy:
                            options
                                .enableHighAccuracy
                            ?? true,
                        timeout:
                            options.timeout
                            || 15000,
                        maximumAge:
                            options.maximumAge
                            || 3000,
                    }
                );

        return state.locationWatchId;
    }

    function stopLocationWatch() {
        if (
            state.locationWatchId
            !== null
        ) {
            navigator.geolocation
                .clearWatch(
                    state.locationWatchId
                );

            state.locationWatchId =
                null;
        }
    }

    async function sendLocation(
        position
    ) {
        const coords =
            position.coords;

        const result =
            await fetchJson(
                `${API}/location`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        latitude:
                            coords.latitude,
                        longitude:
                            coords.longitude,
                        accuracy_meters:
                            coords.accuracy,
                        altitude_meters:
                            coords.altitude,
                        heading_degrees:
                            coords.heading,
                        speed_meters_per_second:
                            coords.speed,
                        captured_at:
                            new Date(
                                position.timestamp
                            ).toISOString(),
                        source:
                            "browser_geolocation",
                    }),
                }
            );

        document.dispatchEvent(
            new CustomEvent(
                "syk:location-updated",
                {
                    detail: result,
                }
            )
        );

        return result;
    }

    async function queryPermission(
        name
    ) {
        if (
            !navigator.permissions
            || !navigator.permissions.query
        ) {
            return "unknown";
        }

        try {
            const result =
                await navigator.permissions
                    .query({
                        name,
                    });

            return result.state;
        }
        catch {
            return "unknown";
        }
    }

    async function refreshPermissions() {
        const mappings = [
            [
                "camera",
                "camera",
            ],
            [
                "microphone",
                "microphone",
            ],
            [
                "geolocation",
                "location",
            ],
        ];

        const result = {};

        for (
            const [
                browserName,
                sensorName,
            ]
            of mappings
        ) {
            const stateValue =
                await queryPermission(
                    browserName
                );

            result[sensorName] =
                stateValue;

            await updatePermission(
                sensorName,
                stateValue
            ).catch(
                () => {}
            );
        }

        return result;
    }

    function blobToBase64(
        blob
    ) {
        return new Promise(
            (resolve, reject) => {
                const reader =
                    new FileReader();

                reader.onerror =
                    () => reject(
                        reader.error
                    );

                reader.onload =
                    () => {
                        const value =
                            String(
                                reader.result
                            );

                        resolve(
                            value.split(
                                ","
                            )[1]
                            || ""
                        );
                    };

                reader.readAsDataURL(
                    blob
                );
            }
        );
    }

    function snapshot() {
        return {
            cameraActive:
                Boolean(
                    state.cameraStream
                ),
            microphoneActive:
                Boolean(
                    state.microphoneStream
                ),
            locationWatching:
                state.locationWatchId
                !== null,
            cameraFacingMode:
                state.cameraFacingMode,
        };
    }

    window.SyKMobileSensors = {
        startCamera,
        stopCamera,
        captureFrame,
        startMicrophone,
        stopMicrophone,
        requestLocation,
        startLocationWatch,
        stopLocationWatch,
        refreshPermissions,
        snapshot,
    };

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            ensureCameraElements();

            refreshPermissions()
                .catch(
                    () => {}
                );
        },
        {
            once: true,
        }
    );
})();