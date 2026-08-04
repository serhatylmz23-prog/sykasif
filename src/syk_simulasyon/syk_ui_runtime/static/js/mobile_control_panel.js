(() => {
    "use strict";

    const API =
        "/api/syk-ui/mobile-control";

    const state = {
        deviceId: null,
        deviceType: "browser",
        cameraActive: false,
        microphoneActive: false,
        locationActive: false,
        notificationPermission:
            "unknown",
        connectionState:
            navigator.onLine
                ? "online"
                : "offline",
        pairingState: "unpaired",
        queueCount: 0,
        fullscreen: false,
        wakeLock: false,
        wakeLockHandle: null,
        panelOpen: false,
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
                || "Mobil kontrol işlemi "
                + "başarısız."
            );
        }

        return payload;
    }

    function resolveDevice() {
        const mobileSnapshot =
            window.SyKMobileRuntime
                ?.snapshot()
                || {};

        state.deviceId =
            mobileSnapshot.deviceId
            || localStorage.getItem(
                "sykasif.mobile.device_id"
            )
            || `SYK-CONTROL-${
                crypto.randomUUID()
            }`;

        state.deviceType =
            mobileSnapshot.profile
                ?.device_type
            || document.body.dataset
                .sykDeviceType
            || "browser";
    }

    async function register() {
        resolveDevice();

        return fetchJson(
            `${API}/devices`,
            {
                method: "POST",
                body: JSON.stringify({
                    device_id:
                        state.deviceId,
                    device_type:
                        state.deviceType,
                }),
            }
        );
    }

    async function patch(
        changes
    ) {
        if (!state.deviceId) {
            await register();
        }

        return fetchJson(
            `${API}/devices/${
                encodeURIComponent(
                    state.deviceId
                )
            }`,
            {
                method: "PATCH",
                body:
                    JSON.stringify(
                        changes
                    ),
            }
        );
    }

    function ensurePanel() {
        let panel =
            document.querySelector(
                "#syk-mobile-control-panel"
            );

        if (panel) {
            return panel;
        }

        panel =
            document.createElement(
                "section"
            );

        panel.id =
            "syk-mobile-control-panel";

        panel.className =
            "syk-mobile-control-panel";

        panel.setAttribute(
            "aria-label",
            "Telefon ve tablet kontrol paneli"
        );

        panel.innerHTML = `
            <header
                class="syk-mobile-control-panel__header"
            >
                <button
                    id="syk-mobile-control-toggle"
                    type="button"
                    aria-expanded="false"
                >
                    <span
                        class="syk-mobile-control-panel__mark"
                        aria-hidden="true"
                    >
                        ✦
                    </span>

                    <span>
                        <strong>
                            Saha Terminali
                        </strong>

                        <small
                            id="syk-mobile-control-summary"
                        >
                            Hazırlanıyor…
                        </small>
                    </span>
                </button>
            </header>

            <div
                id="syk-mobile-control-body"
                class="syk-mobile-control-panel__body"
                hidden
            >
                <div
                    class="syk-mobile-control-status-grid"
                >
                    <article
                        data-control-status="connection"
                    >
                        <strong>
                            Bağlantı
                        </strong>

                        <span>
                            Bilinmiyor
                        </span>
                    </article>

                    <article
                        data-control-status="pairing"
                    >
                        <strong>
                            Cihaz Eşleştirme
                        </strong>

                        <span>
                            Eşleştirilmedi
                        </span>
                    </article>

                    <article
                        data-control-status="queue"
                    >
                        <strong>
                            Bekleyen Veri
                        </strong>

                        <span>
                            0 kayıt
                        </span>
                    </article>

                    <article
                        data-control-status="notification"
                    >
                        <strong>
                            Bildirim
                        </strong>

                        <span>
                            Bilinmiyor
                        </span>
                    </article>
                </div>

                <div
                    class="syk-mobile-control-actions"
                >
                    <button
                        type="button"
                        data-control-action="camera"
                        aria-pressed="false"
                    >
                        Kamera
                    </button>

                    <button
                        type="button"
                        data-control-action="microphone"
                        aria-pressed="false"
                    >
                        Mikrofon
                    </button>

                    <button
                        type="button"
                        data-control-action="location"
                        aria-pressed="false"
                    >
                        GPS
                    </button>

                    <button
                        type="button"
                        data-control-action="notification"
                    >
                        Bildirim İzni
                    </button>

                    <button
                        type="button"
                        data-control-action="pair"
                    >
                        Cihaz Eşleştir
                    </button>

                    <button
                        type="button"
                        data-control-action="sync"
                    >
                        Verileri Eşitle
                    </button>

                    <button
                        type="button"
                        data-control-action="fullscreen"
                        aria-pressed="false"
                    >
                        Tam Ekran
                    </button>

                    <button
                        type="button"
                        data-control-action="wake-lock"
                        aria-pressed="false"
                    >
                        Ekranı Açık Tut
                    </button>
                </div>

                <section
                    id="syk-pairing-area"
                    class="syk-mobile-pairing-area"
                    hidden
                >
                    <h3>
                        Cihaz Eşleştirme
                    </h3>

                    <p>
                        Ana makinede gösterilen
                        altı haneli kodu girin.
                    </p>

                    <form
                        id="syk-pairing-form"
                    >
                        <label
                            for="syk-pairing-code"
                        >
                            Eşleştirme Kodu
                        </label>

                        <input
                            id="syk-pairing-code"
                            type="text"
                            inputmode="numeric"
                            pattern="[0-9]{6}"
                            maxlength="6"
                            autocomplete="one-time-code"
                            placeholder="000000"
                            required
                        >

                        <button
                            type="submit"
                        >
                            Eşleştir
                        </button>
                    </form>
                </section>

                <footer
                    class="syk-mobile-control-panel__footer"
                >
                    <span
                        id="syk-mobile-control-message"
                    >
                        Sistem hazır.
                    </span>
                </footer>
            </div>
        `;

        document.body.appendChild(
            panel
        );

        bindPanel(panel);
        render();

        return panel;
    }

    function bindPanel(
        panel
    ) {
        const toggle =
            panel.querySelector(
                "#syk-mobile-control-toggle"
            );

        const body =
            panel.querySelector(
                "#syk-mobile-control-body"
            );

        toggle.addEventListener(
            "click",
            () => {
                body.hidden =
                    !body.hidden;

                state.panelOpen =
                    !body.hidden;

                toggle.setAttribute(
                    "aria-expanded",
                    String(
                        state.panelOpen
                    )
                );
            }
        );

        for (
            const button
            of panel.querySelectorAll(
                "[data-control-action]"
            )
        ) {
            button.addEventListener(
                "click",
                () => {
                    runAction(
                        button.dataset
                            .controlAction,
                        button
                    ).catch(
                        error => {
                            setMessage(
                                error.message,
                                true
                            );
                        }
                    );
                }
            );
        }

        panel.querySelector(
            "#syk-pairing-form"
        ).addEventListener(
            "submit",
            submitPairing
        );
    }

    async function runAction(
        action,
        button
    ) {
        switch (action) {
            case "camera":
                await toggleCamera(
                    button
                );
                break;

            case "microphone":
                await toggleMicrophone(
                    button
                );
                break;

            case "location":
                await toggleLocation(
                    button
                );
                break;

            case "notification":
                await requestNotifications();
                break;

            case "pair":
                togglePairingArea();
                break;

            case "sync":
                await synchronize();
                break;

            case "fullscreen":
                await toggleFullscreen(
                    button
                );
                break;

            case "wake-lock":
                await toggleWakeLock(
                    button
                );
                break;

            default:
                throw new Error(
                    "Bilinmeyen kontrol işlemi."
                );
        }
    }

    async function toggleCamera(
        button
    ) {
        if (
            !window.SyKMobileSensors
        ) {
            throw new Error(
                "Kamera çalışma ortamı "
                + "hazır değil."
            );
        }

        if (!state.cameraActive) {
            setMessage(
                "Kamera açılıyor…"
            );

            await patch({
                camera_state:
                    "starting",
            });

            try {
                await window
                    .SyKMobileSensors
                    .startCamera({
                        facingMode:
                            "environment",
                    });

                state.cameraActive =
                    true;

                button.setAttribute(
                    "aria-pressed",
                    "true"
                );

                await patch({
                    camera_state:
                        "active",
                    last_error: null,
                });

                setMessage(
                    "Kamera hazır."
                );
            }
            catch (error) {
                await patch({
                    camera_state:
                        "error",
                    last_error:
                        error.message,
                });

                throw error;
            }
        }
        else {
            await patch({
                camera_state:
                    "stopping",
            });

            await window
                .SyKMobileSensors
                .stopCamera();

            state.cameraActive =
                false;

            button.setAttribute(
                "aria-pressed",
                "false"
            );

            await patch({
                camera_state:
                    "idle",
            });

            setMessage(
                "Kamera kapatıldı."
            );
        }

        render();
    }

    async function toggleMicrophone(
        button
    ) {
        if (
            !window.SyKMobileSensors
        ) {
            throw new Error(
                "Mikrofon çalışma ortamı "
                + "hazır değil."
            );
        }

        if (!state.microphoneActive) {
            setMessage(
                "Mikrofon açılıyor…"
            );

            await patch({
                microphone_state:
                    "starting",
            });

            try {
                await window
                    .SyKMobileSensors
                    .startMicrophone({
                        sampleRate:
                            16000,
                        channels: 1,
                    });

                state.microphoneActive =
                    true;

                button.setAttribute(
                    "aria-pressed",
                    "true"
                );

                await patch({
                    microphone_state:
                        "active",
                    last_error: null,
                });

                setMessage(
                    "Mikrofon Kaşif için hazır."
                );
            }
            catch (error) {
                await patch({
                    microphone_state:
                        "error",
                    last_error:
                        error.message,
                });

                throw error;
            }
        }
        else {
            await window
                .SyKMobileSensors
                .stopMicrophone();

            state.microphoneActive =
                false;

            button.setAttribute(
                "aria-pressed",
                "false"
            );

            await patch({
                microphone_state:
                    "idle",
            });

            setMessage(
                "Mikrofon kapatıldı."
            );
        }

        render();
    }

    async function toggleLocation(
        button
    ) {
        if (
            !window.SyKMobileSensors
        ) {
            throw new Error(
                "GPS çalışma ortamı "
                + "hazır değil."
            );
        }

        if (!state.locationActive) {
            await patch({
                location_state:
                    "starting",
            });

            try {
                const location =
                    await window
                        .SyKMobileSensors
                        .requestLocation();

                window
                    .SyKMobileSensors
                    .startLocationWatch();

                state.locationActive =
                    true;

                button.setAttribute(
                    "aria-pressed",
                    "true"
                );

                await patch({
                    location_state:
                        "active",
                    last_error: null,
                });

                setMessage(
                    `GPS hazır. Doğruluk: ${
                        location
                            .accuracy_meters
                    } metre`
                );
            }
            catch (error) {
                await patch({
                    location_state:
                        "error",
                    last_error:
                        error.message,
                });

                throw error;
            }
        }
        else {
            window
                .SyKMobileSensors
                .stopLocationWatch();

            state.locationActive =
                false;

            button.setAttribute(
                "aria-pressed",
                "false"
            );

            await patch({
                location_state:
                    "idle",
            });

            setMessage(
                "GPS takibi durduruldu."
            );
        }

        render();
    }

    async function requestNotifications() {
        if (
            !("Notification" in window)
        ) {
            state.notificationPermission =
                "unsupported";

            await patch({
                notification_permission:
                    "unsupported",
            });

            throw new Error(
                "Bildirim desteği bulunmuyor."
            );
        }

        const permission =
            await Notification
                .requestPermission();

        state.notificationPermission =
            permission;

        await patch({
            notification_permission:
                permission,
        });

        if (
            permission
            === "granted"
        ) {
            new Notification(
                "SyKaşif",
                {
                    body:
                        "Telefon ve tablet "
                        + "bildirimleri hazır.",
                    tag:
                        "sykasif-ready",
                    silent: false,
                }
            );

            setMessage(
                "Bildirim izni verildi."
            );
        }
        else {
            setMessage(
                "Bildirim izni verilmedi.",
                true
            );
        }

        render();
    }

    function togglePairingArea() {
        const area =
            document.querySelector(
                "#syk-pairing-area"
            );

        area.hidden =
            !area.hidden;

        if (!area.hidden) {
            area.querySelector(
                "#syk-pairing-code"
            ).focus();
        }
    }

    async function submitPairing(
        event
    ) {
        event.preventDefault();

        const input =
            document.querySelector(
                "#syk-pairing-code"
            );

        const code =
            input.value
                .replace(/\D/g, "")
                .slice(0, 6);

        if (
            code.length !== 6
        ) {
            throw new Error(
                "Eşleştirme kodu "
                + "altı haneli olmalıdır."
            );
        }

        if (
            !window.SyKMobileOffline
        ) {
            throw new Error(
                "Cihaz eşleştirme çalışma "
                + "ortamı hazır değil."
            );
        }

        state.pairingState =
            "waiting";

        await patch({
            pairing_state:
                "waiting",
        });

        try {
            await window
                .SyKMobileOffline
                .confirmPairing(code);

            state.pairingState =
                "paired";

            await patch({
                pairing_state:
                    "paired",
            });

            input.value = "";

            document.querySelector(
                "#syk-pairing-area"
            ).hidden = true;

            setMessage(
                "Cihaz güvenli biçimde "
                + "eşleştirildi."
            );
        }
        catch (error) {
            state.pairingState =
                "unpaired";

            await patch({
                pairing_state:
                    "unpaired",
                last_error:
                    error.message,
            });

            throw error;
        }

        render();
    }

    async function synchronize() {
        if (
            !window.SyKMobileOffline
        ) {
            throw new Error(
                "Çevrimdışı veri çalışma "
                + "ortamı hazır değil."
            );
        }

        setMessage(
            "Veriler eşitleniyor…"
        );

        const result =
            await window
                .SyKMobileOffline
                .sync();

        setMessage(
            `${result.synced} kayıt `
            + `eşitlendi, `
            + `${result.failed} kayıt `
            + `bekliyor.`
        );
    }

    async function toggleFullscreen(
        button
    ) {
        if (
            !window.SyKMobileRuntime
        ) {
            throw new Error(
                "Tam ekran çalışma ortamı "
                + "hazır değil."
            );
        }

        if (!document.fullscreenElement) {
            await window
                .SyKMobileRuntime
                .enterFullscreen();

            state.fullscreen = true;
        }
        else {
            await window
                .SyKMobileRuntime
                .leaveFullscreen();

            state.fullscreen = false;
        }

        button.setAttribute(
            "aria-pressed",
            String(
                state.fullscreen
            )
        );

        await patch({
            fullscreen:
                state.fullscreen,
        });

        setMessage(
            state.fullscreen
                ? "Tam ekran açıldı."
                : "Tam ekran kapatıldı."
        );
    }

    async function toggleWakeLock(
        button
    ) {
        if (!state.wakeLock) {
            if (
                !("wakeLock" in navigator)
            ) {
                throw new Error(
                    "Ekranı açık tutma "
                    + "özelliği desteklenmiyor."
                );
            }

            state.wakeLockHandle =
                await navigator
                    .wakeLock
                    .request("screen");

            state.wakeLock = true;

            state.wakeLockHandle
                .addEventListener(
                    "release",
                    () => {
                        state.wakeLock =
                            false;

                        render();
                    }
                );
        }
        else {
            await state
                .wakeLockHandle
                ?.release();

            state.wakeLockHandle =
                null;

            state.wakeLock = false;
        }

        button.setAttribute(
            "aria-pressed",
            String(
                state.wakeLock
            )
        );

        await patch({
            wake_lock:
                state.wakeLock,
        });

        setMessage(
            state.wakeLock
                ? "Ekran açık tutulacak."
                : "Ekran kilidi normale döndü."
        );
    }

    function render() {
        const panel =
            document.querySelector(
                "#syk-mobile-control-panel"
            );

        if (!panel) {
            return;
        }

        const connection =
            panel.querySelector(
                '[data-control-status="connection"] span'
            );

        const pairing =
            panel.querySelector(
                '[data-control-status="pairing"] span'
            );

        const queue =
            panel.querySelector(
                '[data-control-status="queue"] span'
            );

        const notification =
            panel.querySelector(
                '[data-control-status="notification"] span'
            );

        connection.textContent =
            state.connectionState
            === "online"
                ? "Çevrimiçi"
                : "Çevrimdışı";

        pairing.textContent = {
            unpaired:
                "Eşleştirilmedi",
            waiting:
                "Onay bekliyor",
            paired:
                "Güvenli cihaz",
            expired:
                "Kod süresi doldu",
            revoked:
                "Yetki kaldırıldı",
        }[
            state.pairingState
        ] || "Bilinmiyor";

        queue.textContent =
            `${state.queueCount} kayıt`;

        notification.textContent = {
            granted:
                "İzin verildi",
            denied:
                "İzin verilmedi",
            default:
                "İzin bekleniyor",
            prompt:
                "İzin bekleniyor",
            unsupported:
                "Desteklenmiyor",
            unknown:
                "Bilinmiyor",
        }[
            state
                .notificationPermission
        ] || "Bilinmiyor";

        const activeCount = [
            state.cameraActive,
            state.microphoneActive,
            state.locationActive,
        ].filter(Boolean).length;

        panel.querySelector(
            "#syk-mobile-control-summary"
        ).textContent =
            `${state.deviceType} · `
            + `${activeCount} sensör etkin`;

        document.body.dataset
            .sykMobileConnection =
                state.connectionState;

        document.body.dataset
            .sykMobilePairing =
                state.pairingState;
    }

    function setMessage(
        message,
        error = false
    ) {
        const element =
            document.querySelector(
                "#syk-mobile-control-message"
            );

        if (!element) {
            return;
        }

        element.textContent =
            message;

        element.dataset.state =
            error
                ? "error"
                : "normal";
    }

    function bindRuntimeEvents() {
        window.addEventListener(
            "online",
            async () => {
                state.connectionState =
                    "online";

                await patch({
                    connection_state:
                        "online",
                }).catch(
                    () => {}
                );

                render();
            }
        );

        window.addEventListener(
            "offline",
            async () => {
                state.connectionState =
                    "offline";

                await patch({
                    connection_state:
                        "offline",
                }).catch(
                    () => {}
                );

                render();
            }
        );

        document.addEventListener(
            "syk:offline-queue-changed",
            async event => {
                state.queueCount =
                    event.detail
                        ?.count
                    || 0;

                await patch({
                    offline_queue_count:
                        state.queueCount,
                }).catch(
                    () => {}
                );

                render();
            }
        );

        document.addEventListener(
            "syk:pairing-confirmed",
            async () => {
                state.pairingState =
                    "paired";

                await patch({
                    pairing_state:
                        "paired",
                }).catch(
                    () => {}
                );

                render();
            }
        );

        document.addEventListener(
            "fullscreenchange",
            () => {
                state.fullscreen =
                    Boolean(
                        document
                            .fullscreenElement
                    );

                render();
            }
        );

        document.addEventListener(
            "visibilitychange",
            async () => {
                if (
                    document.visibilityState
                    === "visible"
                    && state.wakeLock
                    && (
                        !state
                            .wakeLockHandle
                        || state
                            .wakeLockHandle
                            .released
                    )
                ) {
                    try {
                        state.wakeLockHandle =
                            await navigator
                                .wakeLock
                                .request(
                                    "screen"
                                );
                    }
                    catch {
                    }
                }
            }
        );
    }

    async function initialize() {
        ensurePanel();
        bindRuntimeEvents();

        await register();

        if (
            "Notification" in window
        ) {
            state.notificationPermission =
                Notification.permission;
        }
        else {
            state.notificationPermission =
                "unsupported";
        }

        if (
            window.SyKMobileOffline
        ) {
            state.pairingState =
                await window
                    .SyKMobileOffline
                    .verifyPairing()
                    .then(
                        valid =>
                            valid
                                ? "paired"
                                : "unpaired"
                    )
                    .catch(
                        () =>
                            "unpaired"
                    );
        }

        await patch({
            notification_permission:
                state
                    .notificationPermission,
            connection_state:
                state.connectionState,
            pairing_state:
                state.pairingState,
        });

        render();

        document.dispatchEvent(
            new CustomEvent(
                "syk:mobile-control-ready",
                {
                    detail:
                        snapshot(),
                }
            )
        );
    }

    function open() {
        const panel =
            ensurePanel();

        const body =
            panel.querySelector(
                "#syk-mobile-control-body"
            );

        body.hidden = false;

        panel.querySelector(
            "#syk-mobile-control-toggle"
        ).setAttribute(
            "aria-expanded",
            "true"
        );

        state.panelOpen = true;
    }

    function snapshot() {
        return {
            deviceId:
                state.deviceId,
            deviceType:
                state.deviceType,
            cameraActive:
                state.cameraActive,
            microphoneActive:
                state.microphoneActive,
            locationActive:
                state.locationActive,
            notificationPermission:
                state
                    .notificationPermission,
            connectionState:
                state.connectionState,
            pairingState:
                state.pairingState,
            queueCount:
                state.queueCount,
            fullscreen:
                state.fullscreen,
            wakeLock:
                state.wakeLock,
            panelOpen:
                state.panelOpen,
        };
    }

    window.SyKMobileControl = {
        initialize,
        open,
        snapshot,
        requestNotifications,
        synchronize,
    };

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            initialize().catch(
                error => {
                    document.body.dataset
                        .sykMobileControl =
                            "error";

                    setMessage(
                        error.message,
                        true
                    );
                }
            );
        },
        {
            once: true,
        }
    );
})();