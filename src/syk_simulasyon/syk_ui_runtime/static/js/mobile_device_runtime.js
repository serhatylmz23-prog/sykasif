(() => {
    "use strict";

    const API =
        "/api/syk-ui/mobile-runtime";

    const DEVICE_KEY =
        "sykasif.mobile.device_id";

    const state = {
        deviceId: null,
        profile: null,
        capabilities: null,
        registration: null,
        updateTimer: null,
    };

    function getDeviceId() {
        let value =
            localStorage.getItem(
                DEVICE_KEY
            );

        if (!value) {
            value =
                `SYK-WEB-${crypto
                    .randomUUID()
                    .replaceAll("-", "")
                    .slice(0, 20)}`;

            localStorage.setItem(
                DEVICE_KEY,
                value
            );
        }

        return value;
    }

    function orientation() {
        if (
            screen.orientation
            && screen.orientation.type
        ) {
            return (
                screen.orientation.type
                    .startsWith(
                        "portrait"
                    )
                    ? "portrait"
                    : "landscape"
            );
        }

        return (
            window.innerHeight
            >= window.innerWidth
                ? "portrait"
                : "landscape"
        );
    }

    function deviceType() {
        const shortEdge = Math.min(
            window.innerWidth,
            window.innerHeight
        );

        const touch =
            navigator.maxTouchPoints > 0;

        if (
            touch
            && shortEdge < 600
        ) {
            return "phone";
        }

        if (
            touch
            && shortEdge < 1000
        ) {
            return "tablet";
        }

        return "desktop";
    }

    function inputMode() {
        const touch =
            navigator.maxTouchPoints > 0;

        const finePointer =
            window.matchMedia(
                "(pointer: fine)"
            ).matches;

        if (
            touch
            && finePointer
        ) {
            return "hybrid";
        }

        if (touch) {
            return "touch";
        }

        if (finePointer) {
            return "mouse";
        }

        return "unknown";
    }

    function detectCapabilities() {
        return {
            touch:
                navigator.maxTouchPoints > 0,

            camera: Boolean(
                navigator.mediaDevices
                && navigator
                    .mediaDevices
                    .getUserMedia
            ),

            microphone: Boolean(
                navigator.mediaDevices
                && navigator
                    .mediaDevices
                    .getUserMedia
            ),

            location:
                "geolocation"
                in navigator,

            notification:
                "Notification"
                in window,

            vibration:
                "vibrate"
                in navigator,

            fullscreen:
                Boolean(
                    document
                        .documentElement
                        .requestFullscreen
                ),

            wake_lock:
                "wakeLock"
                in navigator,

            online:
                navigator.onLine,

            input_mode:
                inputMode(),
        };
    }

    function viewport() {
        return {
            width:
                Math.round(
                    window.innerWidth
                ),

            height:
                Math.round(
                    window.innerHeight
                ),

            pixel_ratio:
                window.devicePixelRatio
                || 1,

            orientation:
                orientation(),
        };
    }

    function registrationPayload() {
        const type = deviceType();

        return {
            device_id:
                state.deviceId,

            device_type:
                type,

            title:
                type === "phone"
                    ? "SyKaşif Telefonu"
                    : (
                        type === "tablet"
                            ? "SyKaşif Tableti"
                            : "SyKaşif Masaüstü"
                    ),

            platform:
                navigator.userAgentData
                    ?.platform
                || navigator.platform
                || "Tarayıcı",

            user_agent:
                navigator.userAgent,

            language:
                navigator.language
                || "tr-TR",

            timezone:
                Intl.DateTimeFormat()
                    .resolvedOptions()
                    .timeZone
                || "Europe/Istanbul",

            viewport:
                viewport(),

            capabilities:
                detectCapabilities(),

            trusted: false,
        };
    }

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

        let payload = null;

        try {
            payload =
                await response.json();
        }
        catch {
            payload = {};
        }

        if (!response.ok) {
            throw new Error(
                payload.detail
                || "Cihaz çalışma ortamı hatası."
            );
        }

        return payload;
    }

    async function register() {
        state.deviceId =
            getDeviceId();

        const payload =
            await fetchJson(
                `${API}/devices`,
                {
                    method: "POST",
                    body: JSON.stringify(
                        registrationPayload()
                    ),
                }
            );

        state.registration =
            payload.device;

        state.profile =
            payload.layout;

        state.capabilities =
            payload
                .device
                .capabilities;

        applyProfile(
            payload.layout
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:mobile-runtime-ready",
                {
                    detail: payload,
                }
            )
        );

        return payload;
    }

    async function update() {
        if (!state.deviceId) {
            return register();
        }

        const payload =
            await fetchJson(
                `${API}/devices/`
                + encodeURIComponent(
                    state.deviceId
                ),
                {
                    method: "PATCH",
                    body: JSON.stringify({
                        viewport:
                            viewport(),
                        capabilities:
                            detectCapabilities(),
                    }),
                }
            );

        state.registration =
            payload.device;

        state.profile =
            payload.layout;

        state.capabilities =
            payload
                .device
                .capabilities;

        applyProfile(
            payload.layout
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:mobile-runtime-updated",
                {
                    detail: payload,
                }
            )
        );

        return payload;
    }

    function applyProfile(profile) {
        const root =
            document.documentElement;

        const body =
            document.body;

        body.dataset.sykDeviceType =
            profile.device_type;

        body.dataset.sykOrientation =
            profile.orientation;

        body.dataset.sykLayoutDensity =
            profile.density;

        body.dataset.sykNavigationMode =
            profile.navigation_mode;

        body.dataset.sykPanelMode =
            profile.panel_mode;

        root.style.setProperty(
            "--syk-layout-columns",
            String(
                profile.columns
            )
        );

        root.style.setProperty(
            "--syk-touch-target",
            `${profile
                .touch_target_px}px`
        );

        root.style.setProperty(
            "--syk-safe-top",
            "env(safe-area-inset-top, 0px)"
        );

        root.style.setProperty(
            "--syk-safe-right",
            "env(safe-area-inset-right, 0px)"
        );

        root.style.setProperty(
            "--syk-safe-bottom",
            "env(safe-area-inset-bottom, 0px)"
        );

        root.style.setProperty(
            "--syk-safe-left",
            "env(safe-area-inset-left, 0px)"
        );
    }

    function scheduleUpdate() {
        window.clearTimeout(
            state.updateTimer
        );

        state.updateTimer =
            window.setTimeout(
                () => {
                    update().catch(
                        () => {}
                    );
                },
                250
            );
    }

    async function enterFullscreen() {
        const element =
            document.documentElement;

        if (
            !element.requestFullscreen
        ) {
            return false;
        }

        if (!document.fullscreenElement) {
            await element
                .requestFullscreen();

            return true;
        }

        return true;
    }

    async function leaveFullscreen() {
        if (
            document.fullscreenElement
            && document.exitFullscreen
        ) {
            await document
                .exitFullscreen();
        }

        return true;
    }

    async function keepAwake() {
        if (
            !("wakeLock" in navigator)
        ) {
            return null;
        }

        return navigator
            .wakeLock
            .request("screen");
    }

    function vibrate(pattern = 40) {
        if (
            "vibrate" in navigator
        ) {
            return navigator.vibrate(
                pattern
            );
        }

        return false;
    }

    function snapshot() {
        return {
            deviceId:
                state.deviceId,

            profile:
                state.profile,

            capabilities:
                state.capabilities,

            registration:
                state.registration,
        };
    }

    function start() {
        state.deviceId =
            getDeviceId();

        register().catch(
            error => {
                document.body.dataset
                    .sykMobileRuntime =
                        "error";

                document.dispatchEvent(
                    new CustomEvent(
                        "syk:mobile-runtime-error",
                        {
                            detail: {
                                message:
                                    error.message,
                            },
                        }
                    )
                );
            }
        );

        window.addEventListener(
            "resize",
            scheduleUpdate
        );

        window.addEventListener(
            "orientationchange",
            scheduleUpdate
        );

        window.addEventListener(
            "online",
            scheduleUpdate
        );

        window.addEventListener(
            "offline",
            scheduleUpdate
        );

        if (screen.orientation) {
            screen.orientation
                .addEventListener(
                    "change",
                    scheduleUpdate
                );
        }
    }

    window.SyKMobileRuntime = {
        register,
        update,
        snapshot,
        enterFullscreen,
        leaveFullscreen,
        keepAwake,
        vibrate,
    };

    document.addEventListener(
        "DOMContentLoaded",
        start,
        {
            once: true,
        }
    );
})();