(() => {
    "use strict";

    const DEVICE_ID_KEY =
        "sykasif_terminal_v2_device_id";

    const TRUST_TOKEN_KEY =
        "sykasif_terminal_v2_trust_token";

    function detectDeviceType() {
        const width = window.innerWidth;
        const touch =
            navigator.maxTouchPoints > 0
            || "ontouchstart" in window;

        if (!touch) {
            return "desktop";
        }

        if (width >= 600) {
            return "tablet";
        }

        return "phone";
    }

    function detectDeviceName() {
        const type = detectDeviceType();

        if (type === "tablet") {
            return "SyKaşif Tablet";
        }

        if (type === "phone") {
            return "SyKaşif Telefon";
        }

        return "SyKaşif Masaüstü";
    }

    async function postJson(path, payload) {
        const response = await fetch(path, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || `HTTP ${response.status}`,
            );
        }

        return data;
    }

    async function registerDevice() {
        const currentId =
            localStorage.getItem(DEVICE_ID_KEY);

        const result = await postJson(
            "/api/v2/devices/register",
            {
                device_id: currentId,
                device_type: detectDeviceType(),
                device_name: detectDeviceName(),
            },
        );

        const deviceId =
            result.device.device_id;

        localStorage.setItem(
            DEVICE_ID_KEY,
            deviceId,
        );

        if (result.trust_token) {
            localStorage.setItem(
                TRUST_TOKEN_KEY,
                result.trust_token,
            );
        }

        window.dispatchEvent(
            new CustomEvent(
                "sykasif.device.ready",
                {
                    detail: result,
                },
            ),
        );

        return result;
    }

    async function reconnectDevice() {
        const deviceId =
            localStorage.getItem(DEVICE_ID_KEY);

        const trustToken =
            localStorage.getItem(TRUST_TOKEN_KEY);

        if (!deviceId || !trustToken) {
            return registerDevice();
        }

        try {
            const result = await postJson(
                "/api/v2/devices/reconnect",
                {
                    device_id: deviceId,
                    trust_token: trustToken,
                },
            );

            window.dispatchEvent(
                new CustomEvent(
                    "sykasif.device.reconnected",
                    {
                        detail: result,
                    },
                ),
            );

            return result;
        } catch {
            localStorage.removeItem(
                DEVICE_ID_KEY,
            );

            localStorage.removeItem(
                TRUST_TOKEN_KEY,
            );

            return registerDevice();
        }
    }

    async function start() {
        try {
            await reconnectDevice();
        } catch (error) {
            console.error(
                "SyKaşif cihaz bağlantısı kurulamadı:",
                error,
            );

            window.setTimeout(
                start,
                3000,
            );
        }
    }

    window.addEventListener(
        "online",
        start,
    );

    start();
})();
