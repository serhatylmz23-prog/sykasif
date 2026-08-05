(() => {
    "use strict";

    const state = {
        workspace: null,
        layers: new Map(),
        pins: [],
        measurements: [],
        arEnabled: false,
        shallowDepthM: 2.0
    };

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function ensurePanel() {
        let panel = document.querySelector(
            "#syk-map-workspace-panel"
        );

        if (panel) {
            return panel;
        }

        panel = document.createElement("section");
        panel.id = "syk-map-workspace-panel";
        panel.className = "syk-map-workspace-panel";
        panel.hidden = true;

        panel.innerHTML = `
            <header class="syk-map-workspace-header">
                <div>
                    <span class="syk-map-eyebrow">
                        HARİTA ÇALIŞMA ALANI
                    </span>
                    <strong id="syk-map-workspace-title">
                        Aktif çalışma alanı yok
                    </strong>
                </div>

                <div class="syk-map-workspace-status">
                    <span id="syk-map-ar-state">
                        AR Kapalı
                    </span>
                    <span id="syk-map-depth-profile">
                        Sığ kıyı: 0–2 m
                    </span>
                </div>
            </header>

            <div class="syk-map-workspace-layout">
                <aside class="syk-map-layer-panel">
                    <h3>Katmanlar</h3>
                    <div id="syk-map-layer-list"></div>
                </aside>

                <div class="syk-map-canvas" id="syk-map-canvas">
                    <div class="syk-map-grid"></div>

                    <div class="syk-map-shallow-zone">
                        <span>0–2 m kıyı tarama bölgesi</span>
                    </div>

                    <div
                        class="syk-map-sonar-sweep"
                        id="syk-map-sonar-sweep"
                        hidden
                    ></div>

                    <div
                        class="syk-map-ar-overlay"
                        id="syk-map-ar-overlay"
                        hidden
                    >
                        AR KATMANI ETKİN
                    </div>

                    <div id="syk-map-pin-layer"></div>
                    <div id="syk-map-measurement-layer"></div>

                    <div class="syk-map-center-marker">
                        <span></span>
                    </div>
                </div>

                <aside class="syk-map-information-panel">
                    <h3>Canlı Bilgi</h3>

                    <dl>
                        <div>
                            <dt>Merkez</dt>
                            <dd id="syk-map-center">—</dd>
                        </div>
                        <div>
                            <dt>Yakınlaştırma</dt>
                            <dd id="syk-map-zoom">—</dd>
                        </div>
                        <div>
                            <dt>Pin</dt>
                            <dd id="syk-map-pin-count">0</dd>
                        </div>
                        <div>
                            <dt>Ölçüm</dt>
                            <dd id="syk-map-measurement-count">0</dd>
                        </div>
                        <div>
                            <dt>Sonar</dt>
                            <dd id="syk-map-sonar-state">Bekliyor</dd>
                        </div>
                    </dl>
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

        return panel;
    }

    function renderLayers() {
        const list = document.querySelector(
            "#syk-map-layer-list"
        );

        if (!list) {
            return;
        }

        list.innerHTML = "";

        for (const layer of state.layers.values()) {
            const button = document.createElement("button");

            button.type = "button";
            button.className = "syk-map-layer-button";
            button.dataset.layerKey = layer.key;
            button.dataset.visible = String(
                layer.visible !== false
            );

            button.innerHTML = `
                <span>${escapeHtml(layer.name)}</span>
                <small>
                    ${escapeHtml(layer.layer_type)}
                    · %${Math.round(
                        Number(layer.opacity || 0) * 100
                    )}
                </small>
            `;

            button.addEventListener(
                "click",
                () => {
                    layer.visible =
                        layer.visible === false;

                    button.dataset.visible = String(
                        layer.visible
                    );

                    updateSpecialLayers();
                }
            );

            list.appendChild(button);
        }
    }

    function renderPins() {
        const layer = document.querySelector(
            "#syk-map-pin-layer"
        );

        if (!layer) {
            return;
        }

        layer.innerHTML = "";

        state.pins.forEach((pin, index) => {
            const marker = document.createElement("button");

            marker.type = "button";
            marker.className = "syk-map-pin";
            marker.style.left =
                `${22 + ((index * 17) % 62)}%`;
            marker.style.top =
                `${24 + ((index * 13) % 48)}%`;

            marker.title = [
                pin.name,
                pin.latitude,
                pin.longitude
            ].join(" · ");

            marker.innerHTML = `
                <span></span>
                <small>${escapeHtml(pin.name)}</small>
            `;

            layer.appendChild(marker);
        });
    }

    function renderMeasurements() {
        const layer = document.querySelector(
            "#syk-map-measurement-layer"
        );

        if (!layer) {
            return;
        }

        layer.innerHTML = "";

        state.measurements.forEach(
            (measurement, index) => {
                const line = document.createElement("div");

                line.className =
                    "syk-map-measurement-line";

                line.style.transform =
                    `rotate(${18 + (index * 11)}deg)`;

                line.innerHTML = `
                    <span>
                        ${escapeHtml(
                            measurement.value
                        )}
                        ${escapeHtml(
                            measurement.unit
                        )}
                    </span>
                `;

                layer.appendChild(line);
            }
        );
    }

    function updateSpecialLayers() {
        const sonarLayer = state.layers.get(
            "garmin-sonar"
        );

        const sonarActive = Boolean(
            sonarLayer
            && sonarLayer.visible !== false
        );

        const sonarSweep = document.querySelector(
            "#syk-map-sonar-sweep"
        );

        if (sonarSweep) {
            sonarSweep.hidden = !sonarActive;
        }

        const sonarState = document.querySelector(
            "#syk-map-sonar-state"
        );

        if (sonarState) {
            sonarState.textContent = sonarActive
                ? "Katman etkin"
                : "Bekliyor";
        }

        const arOverlay = document.querySelector(
            "#syk-map-ar-overlay"
        );

        if (arOverlay) {
            arOverlay.hidden = !state.arEnabled;
        }
    }

    function renderWorkspace(workspace) {
        state.workspace = workspace;
        state.arEnabled = Boolean(
            workspace.ar_enabled
        );
        state.pins = Array.isArray(workspace.pins)
            ? workspace.pins
            : [];
        state.measurements = Array.isArray(
            workspace.measurements
        )
            ? workspace.measurements
            : [];

        state.layers.clear();

        for (
            const layer
            of workspace.layers || []
        ) {
            state.layers.set(
                layer.key,
                {...layer}
            );
        }

        const panel = ensurePanel();
        panel.hidden = false;

        const moduleView = document.querySelector(
            "#module-view"
        );

        if (moduleView) {
            moduleView.hidden = false;
            moduleView.dataset.activeModule =
                "map-workspace";
        }

        const mapStage = document.querySelector(
            "#map-stage"
        );

        if (mapStage) {
            mapStage.hidden = true;
        }

        const frame = document.querySelector(
            "#syframe"
        );

        if (frame) {
            frame.hidden = true;
        }

        document.querySelector(
            "#syk-map-workspace-title"
        ).textContent = workspace.name;

        document.querySelector(
            "#syk-map-ar-state"
        ).textContent = state.arEnabled
            ? "AR Açık"
            : "AR Kapalı";

        document.querySelector(
            "#syk-map-center"
        ).textContent =
            `${workspace.center.latitude.toFixed(6)}, ` +
            `${workspace.center.longitude.toFixed(6)}`;

        document.querySelector(
            "#syk-map-zoom"
        ).textContent = String(workspace.zoom);

        document.querySelector(
            "#syk-map-pin-count"
        ).textContent = String(state.pins.length);

        document.querySelector(
            "#syk-map-measurement-count"
        ).textContent = String(
            state.measurements.length
        );

        renderLayers();
        renderPins();
        renderMeasurements();
        updateSpecialLayers();

        document.dispatchEvent(
            new CustomEvent(
                "syk:map-workspace-rendered",
                {
                    detail: {
                        workspaceId:
                            workspace.workspace_id,
                        pinCount: state.pins.length,
                        layerCount: state.layers.size
                    }
                }
            )
        );
    }

    async function fetchWorkspace(workspaceId) {
        const response = await fetch(
            `/api/syk-ui/map-workspaces/` +
            encodeURIComponent(workspaceId)
        );

        if (!response.ok) {
            throw new Error(
                `Harita alanı alınamadı: ` +
                `${response.status}`
            );
        }

        return response.json();
    }

    async function openWorkspace(workspaceId) {
        const workspace = await fetchWorkspace(
            workspaceId
        );

        renderWorkspace(workspace);

        return workspace;
    }

    function closeWorkspace() {
        const panel = ensurePanel();
        panel.hidden = true;

        state.workspace = null;
        state.layers.clear();
        state.pins = [];
        state.measurements = [];
    }

    document.addEventListener(
        "syk:map-workspace-open",
        (event) => {
            const workspaceId =
                event.detail?.workspaceId;

            if (!workspaceId) {
                return;
            }

            openWorkspace(workspaceId).catch(
                (error) => {
                    console.error(error);
                }
            );
        }
    );

    document.addEventListener(
        "DOMContentLoaded",
        ensurePanel
    );

    window.SyKMapWorkspaceView = {
        open: openWorkspace,
        close: closeWorkspace,
        render: renderWorkspace,
        snapshot() {
            return {
                workspace: state.workspace,
                layers: Array.from(
                    state.layers.values()
                ),
                pins: [...state.pins],
                measurements: [
                    ...state.measurements
                ],
                arEnabled: state.arEnabled,
                shallowDepthM:
                    state.shallowDepthM
            };
        }
    };
})();