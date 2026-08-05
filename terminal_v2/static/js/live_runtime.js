(() => {
    "use strict";

    const runtimeStatus =
        document.getElementById("runtime-status");

    const tabletStatus =
        document.getElementById("tablet-status");

    const streamStatus =
        document.getElementById("stream-status");

    const lastCheck =
        document.getElementById("last-check");

    const latencyStatus =
        document.getElementById("latency-status");

    const sidebarRuntimeStatus =
        document.getElementById("sidebar-runtime-status");

    const topStatusText =
        document.getElementById("top-status-text");

    const topStatusTime =
        document.getElementById("top-status-time");

    function timeNow() {
        return new Date().toLocaleTimeString(
            "tr-TR",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            },
        );
    }

    function applyMetrics(payload) {
        const activeConnections =
            Number(payload.active_connections ?? 0);

        const activeTablets =
            Number(payload.active_tablet ?? 0);

        runtimeStatus.textContent = "ONLINE";
        sidebarRuntimeStatus.textContent = "ONLINE";
        streamStatus.textContent = "SSE V2 ONLINE";

        tabletStatus.textContent =
            activeTablets > 0
                ? `${activeTablets} TABLET BAĞLI`
                : "TABLET BEKLENİYOR";

        latencyStatus.textContent =
            `${activeConnections} CANLI BAĞLANTI`;

        lastCheck.textContent = timeNow();
        topStatusText.textContent = "ÇEVRİMİÇİ";
        topStatusTime.textContent = timeNow();
    }

    function connect() {
        const source = new EventSource(
            "/api/v2/events",
        );

        source.addEventListener(
            "terminal.metrics",
            (event) => {
                try {
                    applyMetrics(
                        JSON.parse(event.data),
                    );
                } catch {
                    streamStatus.textContent =
                        "VERİ HATASI";
                }
            },
        );

        source.addEventListener(
            "open",
            () => {
                streamStatus.textContent =
                    "SSE V2 ONLINE";
            },
        );

        source.addEventListener(
            "error",
            () => {
                streamStatus.textContent =
                    "YENİDEN BAĞLANIYOR";
            },
        );
    }

    connect();
})();
