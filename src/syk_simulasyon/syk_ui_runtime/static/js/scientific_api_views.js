(() => {
    const moduleIds = new Set([
        "geology",
        "frequency",
        "lidar",
        "astronomy",
        "chemistry",
        "spectral",
        "thermal",
        "magnetometer",
        "gravimeter",
        "ert",
        "gpr",
        "seismic",
        "hydro",
        "botany",
        "soil",
        "water",
    ]);

    const sockets = new Map();

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function formatValue(value, unit = "") {
        const cleanValue = escapeHtml(value);
        const cleanUnit = escapeHtml(unit);

        return cleanUnit
            ? `${cleanValue} ${cleanUnit}`
            : cleanValue;
    }

    function renderMetrics(metrics) {
        return metrics.map((metric) => `
            <article
                class="scientific-metric"
                data-metric-id="${escapeHtml(metric.id)}"
            >
                <span>${escapeHtml(metric.title)}</span>

                <strong>
                    ${formatValue(metric.value, metric.unit)}
                </strong>

                <em>
                    ${escapeHtml(metric.note || "Runtime verisi")}
                </em>
            </article>
        `).join("");
    }

    function renderLayers(layers) {
        return layers.map((layer) => `
            <div
                class="scientific-layer"
                data-layer-id="${escapeHtml(layer.id)}"
                data-enabled="${Boolean(layer.enabled)}"
            >
                <span>${escapeHtml(layer.title)}</span>
                <strong>${escapeHtml(layer.state)}</strong>
            </div>
        `).join("");
    }

    function createWavePoints(seed) {
        const points = [];

        for (let index = 0; index <= 40; index += 1) {
            const x = index * 25;

            const y =
                35 +
                Math.sin((index + seed) * 0.72) * 17 +
                Math.sin((index + seed) * 1.87) * 7;

            points.push(`${x},${y.toFixed(2)}`);
        }

        return points.join(" ");
    }

    function renderScreen(payload) {
        const definition = payload.definition;
        const state = payload.state;
        const seed = Math.max(1, state.sequence);

        return `
            <section
                class="scientific-screen module-${escapeHtml(definition.id)}"
                data-scientific-module="${escapeHtml(definition.id)}"
                data-runtime-source="${escapeHtml(state.source)}"
                data-runtime-status="${escapeHtml(state.status)}"
                data-runtime-sequence="${state.sequence}"
            >
                <header class="scientific-header">
                    <div class="scientific-title">
                        <strong>${escapeHtml(definition.title)}</strong>
                        <span>${escapeHtml(definition.subtitle)}</span>
                    </div>

                    <div class="scientific-runtime-state">
                        CANLI RUNTIME BAĞLANTISI
                    </div>
                </header>

                <div class="scientific-runtime-meta">
                    <span>
                        Kaynak:
                        <strong id="scientific-source">
                            ${escapeHtml(state.source)}
                        </strong>
                    </span>

                    <span>
                        Durum:
                        <strong id="scientific-status">
                            ${escapeHtml(state.status)}
                        </strong>
                    </span>

                    <span>
                        Sıra:
                        <strong id="scientific-sequence">
                            ${state.sequence}
                        </strong>
                    </span>

                    <span>
                        Güncelleme:
                        <strong id="scientific-updated-at">
                            ${escapeHtml(state.updated_at)}
                        </strong>
                    </span>
                </div>

                <div class="scientific-layout">
                    <div class="scientific-main">
                        <section class="scientific-scan">
                            <div class="scientific-grid"></div>
                            <div class="scientific-axis"></div>

                            <span class="scientific-orbit one"></span>
                            <span class="scientific-orbit two"></span>
                            <span class="scientific-orbit three"></span>
                            <span class="scientific-core"></span>

                            <span class="scientific-mark a"></span>
                            <span class="scientific-mark b"></span>
                            <span class="scientific-mark c"></span>

                            <span class="scientific-scan-label">
                                CANLI DEĞER
                            </span>

                            <strong
                                id="scientific-live-value"
                                class="scientific-scan-value"
                            >
                                ${formatValue(
                                    state.live_value,
                                    definition.primary_unit,
                                )}
                            </strong>

                            <div class="scientific-wave">
                                <svg
                                    viewBox="0 0 1000 70"
                                    preserveAspectRatio="none"
                                    aria-hidden="true"
                                >
                                    <polyline
                                        points="${createWavePoints(seed)}"
                                    ></polyline>
                                </svg>
                            </div>
                        </section>

                        <section class="scientific-metrics">
                            ${renderMetrics(definition.metrics)}
                        </section>
                    </div>

                    <aside class="scientific-side">
                        <section class="scientific-card">
                            <h3>RUNTIME BİLGİLERİ</h3>

                            <div class="scientific-field">
                                <span>Modül</span>
                                <strong>${escapeHtml(definition.id)}</strong>
                            </div>

                            <div class="scientific-field">
                                <span>Birim</span>
                                <strong>
                                    ${escapeHtml(definition.primary_unit)}
                                </strong>
                            </div>

                            <div class="scientific-field">
                                <span>Kaynak</span>
                                <strong>
                                    ${escapeHtml(state.source)}
                                </strong>
                            </div>

                            <div class="scientific-field">
                                <span>Durum</span>
                                <strong>
                                    ${escapeHtml(state.status)}
                                </strong>
                            </div>
                        </section>

                        <section class="scientific-card">
                            <h3>KATMANLAR</h3>

                            <div class="scientific-layer-list">
                                ${renderLayers(definition.layers)}
                            </div>
                        </section>

                        <section class="scientific-card">
                            <h3>DİJİTAL GÜVEN</h3>

                            <div class="scientific-confidence">
                                <strong id="scientific-confidence">
                                    %${state.confidence}
                                </strong>

                                <div class="scientific-confidence-bar">
                                    <div
                                        id="scientific-confidence-bar"
                                        style="width:${state.confidence}%"
                                    ></div>
                                </div>
                            </div>
                        </section>

                        <div class="scientific-warning">
                            ${escapeHtml(payload.warning)}
                        </div>
                    </aside>
                </div>
            </section>
        `;
    }

    function updateRuntimeFields(payload, container) {
        const definition = payload.definition;
        const state = payload.state;

        const screen = container.querySelector(
            ".scientific-screen"
        );

        if (!screen) {
            return;
        }

        screen.dataset.runtimeSource = state.source;
        screen.dataset.runtimeStatus = state.status;
        screen.dataset.runtimeSequence = state.sequence;

        const liveValue = container.querySelector(
            "#scientific-live-value"
        );

        if (liveValue) {
            liveValue.textContent = formatValue(
                state.live_value,
                definition.primary_unit,
            );
        }

        const confidence = container.querySelector(
            "#scientific-confidence"
        );

        if (confidence) {
            confidence.textContent = `%${state.confidence}`;
        }

        const confidenceBar = container.querySelector(
            "#scientific-confidence-bar"
        );

        if (confidenceBar) {
            confidenceBar.style.width =
                `${state.confidence}%`;
        }

        const source = container.querySelector(
            "#scientific-source"
        );

        if (source) {
            source.textContent = state.source;
        }

        const status = container.querySelector(
            "#scientific-status"
        );

        if (status) {
            status.textContent = state.status;
        }

        const sequence = container.querySelector(
            "#scientific-sequence"
        );

        if (sequence) {
            sequence.textContent = state.sequence;
        }

        const updatedAt = container.querySelector(
            "#scientific-updated-at"
        );

        if (updatedAt) {
            updatedAt.textContent = state.updated_at;
        }
    }

    function closeSocket(containerId) {
        const existing = sockets.get(containerId);

        if (existing) {
            existing.close();
            sockets.delete(containerId);
        }
    }

    function connectLive(moduleId, container) {
        const containerId = container.id || "module-view";

        closeSocket(containerId);

        const protocol =
            window.location.protocol === "https:"
                ? "wss"
                : "ws";

        const url =
            `${protocol}://${window.location.host}` +
            `/api/syk-ui/scientific-modules/` +
            `${encodeURIComponent(moduleId)}/live`;

        const socket = new WebSocket(url);
        sockets.set(containerId, socket);

        socket.addEventListener("message", (event) => {
            const payload = JSON.parse(event.data);

            if (
                container.dataset.activeScientificModule
                !== moduleId
            ) {
                return;
            }

            updateRuntimeFields(payload, container);
        });

        socket.addEventListener("close", () => {
            if (
                container.dataset.activeScientificModule
                === moduleId
            ) {
                setTimeout(
                    () => connectLive(moduleId, container),
                    1500,
                );
            }
        });
    }

    async function mount(moduleId, container) {
        container.dataset.activeScientificModule = moduleId;

        container.innerHTML = `
            <section class="scientific-api-loading">
                <strong>Bilimsel runtime yükleniyor</strong>
                <span>${escapeHtml(moduleId)}</span>
            </section>
        `;

        try {
            const response = await fetch(
                `/api/syk-ui/scientific-modules/` +
                `${encodeURIComponent(moduleId)}`
            );

            if (!response.ok) {
                throw new Error(
                    `Bilimsel runtime hatası: ${response.status}`
                );
            }

            const payload = await response.json();

            if (
                container.dataset.activeScientificModule
                !== moduleId
            ) {
                return;
            }

            container.innerHTML = renderScreen(payload);
            connectLive(moduleId, container);
        }
        catch (error) {
            const fallback =
                window.SyKScientificViews?.render(moduleId);

            if (fallback) {
                container.innerHTML = fallback;
            }
            else {
                container.innerHTML = `
                    <section class="scientific-api-error">
                        <strong>Bilimsel ekran açılamadı</strong>
                        <span>${escapeHtml(error.message)}</span>
                    </section>
                `;
            }
        }
    }

    window.SyKScientificApiViews = {
        has(moduleId) {
            return moduleIds.has(moduleId);
        },

        mount,
    };
})();