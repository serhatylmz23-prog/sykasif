(() => {
    "use strict";

    const state = {
        session: null,
        pollingTimer: null,
        pollingIntervalMs: 1200,
        busy: false
    };

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function ensurePanel() {
        let panel = document.querySelector(
            "#syk-sonar-session-panel"
        );

        if (panel) {
            return panel;
        }

        panel = document.createElement("section");
        panel.id = "syk-sonar-session-panel";
        panel.className = "syk-sonar-session-panel";
        panel.hidden = true;

        panel.innerHTML = `
            <header class="syk-sonar-header">
                <div>
                    <span class="syk-sonar-eyebrow">
                        CANLI SONAR OTURUMU
                    </span>

                    <strong id="syk-sonar-session-name">
                        Oturum seçilmedi
                    </strong>
                </div>

                <div class="syk-sonar-status-group">
                    <span
                        id="syk-sonar-device-state"
                        data-state="disconnected"
                    >
                        Cihaz bekliyor
                    </span>

                    <span
                        id="syk-sonar-session-state"
                        data-state="ready"
                    >
                        Hazır
                    </span>

                    <span id="syk-sonar-depth-profile">
                        0–2 m kıyı profili
                    </span>
                </div>
            </header>

            <div class="syk-sonar-layout">
                <aside class="syk-sonar-left-panel">
                    <h3>Anlık Veri</h3>

                    <dl>
                        <div>
                            <dt>Derinlik</dt>
                            <dd id="syk-sonar-depth">—</dd>
                        </div>

                        <div>
                            <dt>Su sıcaklığı</dt>
                            <dd id="syk-sonar-temperature">—</dd>
                        </div>

                        <div>
                            <dt>Dip sınıfı</dt>
                            <dd id="syk-sonar-bottom">—</dd>
                        </div>

                        <div>
                            <dt>Balık hedefi</dt>
                            <dd id="syk-sonar-fish-count">0</dd>
                        </div>

                        <div>
                            <dt>GPS</dt>
                            <dd id="syk-sonar-gps">—</dd>
                        </div>
                    </dl>

                    <div class="syk-sonar-actions">
                        <button
                            type="button"
                            id="syk-sonar-start"
                        >
                            Oturumu Başlat
                        </button>

                        <button
                            type="button"
                            id="syk-sonar-capture"
                        >
                            Kare Al
                        </button>

                        <button
                            type="button"
                            id="syk-sonar-stop"
                        >
                            Durdur
                        </button>
                    </div>
                </aside>

                <main class="syk-sonar-display">
                    <div class="syk-sonar-water-column">
                        <div class="syk-sonar-surface-line"></div>

                        <div
                            class="syk-sonar-depth-marker"
                            id="syk-sonar-depth-marker"
                        ></div>

                        <div
                            class="syk-sonar-target-layer"
                            id="syk-sonar-target-layer"
                        ></div>

                        <div
                            class="syk-sonar-bottom-line"
                            id="syk-sonar-bottom-line"
                        ></div>

                        <div class="syk-sonar-sweep"></div>

                        <div class="syk-sonar-depth-scale">
                            <span>0 m</span>
                            <span>0,5 m</span>
                            <span>1 m</span>
                            <span>1,5 m</span>
                            <span>2 m</span>
                        </div>
                    </div>

                    <div class="syk-sonar-timeline">
                        <div
                            id="syk-sonar-timeline-bars"
                            class="syk-sonar-timeline-bars"
                        ></div>
                    </div>
                </main>

                <aside class="syk-sonar-right-panel">
                    <h3>Oturum Özeti</h3>

                    <dl>
                        <div>
                            <dt>Kare</dt>
                            <dd id="syk-sonar-frame-count">0</dd>
                        </div>

                        <div>
                            <dt>Ortalama derinlik</dt>
                            <dd id="syk-sonar-average-depth">—</dd>
                        </div>

                        <div>
                            <dt>GPS izi</dt>
                            <dd id="syk-sonar-gps-count">0</dd>
                        </div>

                        <div>
                            <dt>Kanıt adayı</dt>
                            <dd id="syk-sonar-evidence-count">0</dd>
                        </div>

                        <div>
                            <dt>Harita katmanı</dt>
                            <dd id="syk-sonar-map-layer">Bekliyor</dd>
                        </div>
                    </dl>

                    <div
                        id="syk-sonar-warning"
                        class="syk-sonar-warning"
                        hidden
                    ></div>
                </aside>
            </div>
        `;

        const moduleView = document.querySelector(
            "#module-view"
        );

        if (moduleView) {
            moduleView.appendChild(panel);
        }
        else {
            document.body.appendChild(panel);
        }

        installActions(panel);

        return panel;
    }

    function installActions(panel) {
        panel.querySelector(
            "#syk-sonar-start"
        )?.addEventListener(
            "click",
            async () => {
                if (!state.session || state.busy) {
                    return;
                }

                await startSession(
                    state.session.session_id
                );
            }
        );

        panel.querySelector(
            "#syk-sonar-capture"
        )?.addEventListener(
            "click",
            async () => {
                if (!state.session || state.busy) {
                    return;
                }

                await captureFrames(
                    state.session.session_id,
                    1
                );
            }
        );

        panel.querySelector(
            "#syk-sonar-stop"
        )?.addEventListener(
            "click",
            async () => {
                if (!state.session || state.busy) {
                    return;
                }

                await stopSession(
                    state.session.session_id
                );
            }
        );
    }

    async function apiRequest(
        method,
        path,
        payload = null
    ) {
        const options = {
            method,
            headers: {}
        };

        if (payload !== null) {
            options.headers["Content-Type"] =
                "application/json";

            options.body = JSON.stringify(payload);
        }

        const response = await fetch(
            path,
            options
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || `HTTP ${response.status}`
            );
        }

        return data;
    }

    function stateLabel(value) {
        const labels = {
            ready: "Hazır",
            active: "Çalışıyor",
            stopped: "Durdu",
            error: "Hata"
        };

        return labels[value] || value || "Bilinmiyor";
    }

    function renderTargets(session) {
        const targetLayer = document.querySelector(
            "#syk-sonar-target-layer"
        );

        if (!targetLayer) {
            return;
        }

        targetLayer.innerHTML = "";

        const timeline = Array.isArray(
            session.timeline
        )
            ? session.timeline
            : [];

        const fishEntries = timeline.filter(
            (entry) =>
                Number(entry.fish_target_count) > 0
        );

        fishEntries.slice(-14).forEach(
            (entry, index) => {
                const marker =
                    document.createElement("div");

                marker.className =
                    "syk-sonar-fish-target";

                marker.style.left =
                    `${12 + ((index * 13) % 76)}%`;

                const depthRatio = Math.min(
                    Number(entry.depth_m || 0)
                        / Number(
                            session.maximum_priority_depth_m
                            || 2
                        ),
                    1
                );

                marker.style.top =
                    `${10 + (depthRatio * 72)}%`;

                marker.innerHTML = `
                    <span></span>
                    <small>
                        ${escapeHtml(
                            entry.depth_m
                        )} m
                    </small>
                `;

                targetLayer.appendChild(marker);
            }
        );
    }

    function renderTimeline(session) {
        const container = document.querySelector(
            "#syk-sonar-timeline-bars"
        );

        if (!container) {
            return;
        }

        container.innerHTML = "";

        const timeline = Array.isArray(
            session.timeline
        )
            ? session.timeline.slice(-32)
            : [];

        const maximumDepth = Number(
            session.maximum_priority_depth_m
            || 2
        );

        timeline.forEach((entry) => {
            const bar = document.createElement(
                "div"
            );

            bar.className =
                "syk-sonar-timeline-bar";

            const ratio = Math.min(
                Number(entry.depth_m || 0)
                    / maximumDepth,
                1
            );

            bar.style.height =
                `${Math.max(8, ratio * 100)}%`;

            bar.dataset.fish = String(
                Number(
                    entry.fish_target_count
                    || 0
                ) > 0
            );

            bar.title = [
                `${entry.depth_m} m`,
                entry.bottom_classification,
                `Balık: ${entry.fish_target_count}`
            ].join(" · ");

            container.appendChild(bar);
        });
    }

    function renderSession(session) {
        state.session = session;

        const panel = ensurePanel();
        panel.hidden = false;

        const moduleView = document.querySelector(
            "#module-view"
        );

        if (moduleView) {
            moduleView.hidden = false;
            moduleView.dataset.activeModule =
                "sonar-session";
        }

        document.querySelector(
            "#map-stage"
        )?.setAttribute(
            "hidden",
            ""
        );

        document.querySelector(
            "#syframe"
        )?.setAttribute(
            "hidden",
            ""
        );

        const timeline = Array.isArray(
            session.timeline
        )
            ? session.timeline
            : [];

        const latest = timeline.length
            ? timeline[timeline.length - 1]
            : null;

        const summary = session.summary || {};
        const mapLayer =
            session.map_layer_state || {};

        document.querySelector(
            "#syk-sonar-session-name"
        ).textContent = session.name;

        const sessionState = document.querySelector(
            "#syk-sonar-session-state"
        );

        sessionState.textContent = stateLabel(
            session.state
        );

        sessionState.dataset.state =
            session.state;

        const deviceState = document.querySelector(
            "#syk-sonar-device-state"
        );

        deviceState.textContent =
            session.state === "active"
                ? "Cihaz bağlı"
                : "Cihaz hazır";

        deviceState.dataset.state =
            session.state === "active"
                ? "connected"
                : "ready";

        document.querySelector(
            "#syk-sonar-depth"
        ).textContent = latest
            ? `${Number(latest.depth_m).toFixed(2)} m`
            : "—";

        document.querySelector(
            "#syk-sonar-temperature"
        ).textContent = (
            latest
            && latest.water_temperature_c !== null
        )
            ? `${Number(
                latest.water_temperature_c
            ).toFixed(1)} °C`
            : "—";

        document.querySelector(
            "#syk-sonar-bottom"
        ).textContent = latest
            ? latest.bottom_classification
            : "—";

        document.querySelector(
            "#syk-sonar-fish-count"
        ).textContent = String(
            summary.fish_target_count || 0
        );

        document.querySelector(
            "#syk-sonar-gps"
        ).textContent = latest
            && latest.latitude !== null
            && latest.longitude !== null
            ? (
                `${Number(
                    latest.latitude
                ).toFixed(6)}, ` +
                `${Number(
                    latest.longitude
                ).toFixed(6)}`
            )
            : "—";

        document.querySelector(
            "#syk-sonar-frame-count"
        ).textContent = String(
            session.frame_count || 0
        );

        document.querySelector(
            "#syk-sonar-average-depth"
        ).textContent = (
            summary.average_depth_m !== null
            && summary.average_depth_m !== undefined
        )
            ? `${Number(
                summary.average_depth_m
            ).toFixed(2)} m`
            : "—";

        document.querySelector(
            "#syk-sonar-gps-count"
        ).textContent = String(
            Array.isArray(session.gps_track)
                ? session.gps_track.length
                : 0
        );

        document.querySelector(
            "#syk-sonar-evidence-count"
        ).textContent = String(
            Array.isArray(
                session.evidence_candidate_ids
            )
                ? session.evidence_candidate_ids.length
                : 0
        );

        document.querySelector(
            "#syk-sonar-map-layer"
        ).textContent = mapLayer.visible
            ? "Canlı"
            : "Bekliyor";

        const warning = document.querySelector(
            "#syk-sonar-warning"
        );

        if (
            latest
            && Number(latest.depth_m)
                > Number(
                    session.maximum_priority_depth_m
                    || 2
                )
        ) {
            warning.hidden = false;
            warning.textContent =
                "Öncelikli 0–2 m kıyı profili aşıldı.";
        }
        else {
            warning.hidden = true;
            warning.textContent = "";
        }

        const marker = document.querySelector(
            "#syk-sonar-depth-marker"
        );

        if (marker) {
            const depthRatio = latest
                ? Math.min(
                    Number(latest.depth_m)
                    / Number(
                        session.maximum_priority_depth_m
                        || 2
                    ),
                    1
                )
                : 0;

            marker.style.top =
                `${8 + (depthRatio * 78)}%`;
        }

        const bottomLine = document.querySelector(
            "#syk-sonar-bottom-line"
        );

        if (bottomLine) {
            bottomLine.dataset.bottom =
                latest?.bottom_classification
                || "unknown";
        }

        renderTargets(session);
        renderTimeline(session);

        document.dispatchEvent(
            new CustomEvent(
                "syk:sonar-session-rendered",
                {
                    detail: {
                        sessionId:
                            session.session_id,
                        frameCount:
                            session.frame_count || 0,
                        fishTargetCount:
                            summary.fish_target_count
                            || 0
                    }
                }
            )
        );
    }

    async function openSession(sessionId) {
        const session = await apiRequest(
            "GET",
            (
                "/api/syk-ui/sonar-sessions/"
                + encodeURIComponent(sessionId)
            )
        );

        renderSession(session);

        return session;
    }

    async function startSession(sessionId) {
        state.busy = true;

        try {
            const session = await apiRequest(
                "POST",
                (
                    "/api/syk-ui/sonar-sessions/"
                    + encodeURIComponent(sessionId)
                    + "/start"
                )
            );

            renderSession(session);
            beginPolling(sessionId);

            return session;
        }
        finally {
            state.busy = false;
        }
    }

    async function captureFrames(
        sessionId,
        frameCount = 1
    ) {
        state.busy = true;

        try {
            const session = await apiRequest(
                "POST",
                (
                    "/api/syk-ui/sonar-sessions/"
                    + encodeURIComponent(sessionId)
                    + "/capture"
                ),
                {
                    frame_count: frameCount
                }
            );

            renderSession(session);

            return session;
        }
        finally {
            state.busy = false;
        }
    }

    async function stopSession(sessionId) {
        state.busy = true;

        try {
            const session = await apiRequest(
                "POST",
                (
                    "/api/syk-ui/sonar-sessions/"
                    + encodeURIComponent(sessionId)
                    + "/stop"
                )
            );

            endPolling();
            renderSession(session);

            return session;
        }
        finally {
            state.busy = false;
        }
    }

    function beginPolling(sessionId) {
        endPolling();

        state.pollingTimer = window.setInterval(
            () => {
                if (!state.busy) {
                    captureFrames(
                        sessionId,
                        1
                    ).catch(console.error);
                }
            },
            state.pollingIntervalMs
        );
    }

    function endPolling() {
        if (state.pollingTimer !== null) {
            window.clearInterval(
                state.pollingTimer
            );

            state.pollingTimer = null;
        }
    }

    function closePanel() {
        endPolling();

        const panel = ensurePanel();
        panel.hidden = true;
        state.session = null;
    }

    document.addEventListener(
        "syk:sonar-session-open",
        (event) => {
            const sessionId =
                event.detail?.sessionId;

            if (!sessionId) {
                return;
            }

            openSession(sessionId).catch(
                console.error
            );
        }
    );

    document.addEventListener(
        "DOMContentLoaded",
        ensurePanel
    );

    window.SyKSonarSessionPanel = {
        open: openSession,
        start: startSession,
        capture: captureFrames,
        stop: stopSession,
        render: renderSession,
        close: closePanel,
        beginPolling,
        endPolling,
        snapshot() {
            return {
                session: state.session,
                polling: (
                    state.pollingTimer !== null
                ),
                busy: state.busy
            };
        }
    };
})();