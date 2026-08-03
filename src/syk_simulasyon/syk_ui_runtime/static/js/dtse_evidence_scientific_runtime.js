(() => {
    "use strict";

    const TAB_RULES = {
        surface: {
            aliases: [
                "geology",
                "jeoloji",
                "lidar",
                "toprak",
                "soil",
                "material",
                "materyal",
            ],
            fallbackTitle: "Yüzey İncelemesi",
        },

        geometry: {
            aliases: [
                "lidar",
                "gpr",
                "ert",
                "electric",
                "elektrik",
                "sismik",
                "seismic",
                "gravimetre",
                "gravimetry",
            ],
            fallbackTitle: "Geometri İncelemesi",
        },

        thermal: {
            aliases: [
                "thermal",
                "termal",
            ],
            fallbackTitle: "Termal İncelemesi",
        },

        spectral: {
            aliases: [
                "spectral",
                "spektral",
                "chemical",
                "kimyasal",
                "material",
                "materyal",
                "water",
                "su",
            ],
            fallbackTitle: "Spektral İncelemesi",
        },
    };

    const runtimeState = {
        inventory: [],
        inventoryLoaded: false,
        inventoryPromise: null,
        activeTab: null,
        activeSockets: new Map(),
        modulePayloads: new Map(),
        selectedModules: [],
        renderSequence: 0,
    };

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function normalize(value) {
        return String(value ?? "")
            .trim()
            .toLocaleLowerCase("tr-TR")
            .replaceAll("ı", "i")
            .replaceAll("ğ", "g")
            .replaceAll("ü", "u")
            .replaceAll("ş", "s")
            .replaceAll("ö", "o")
            .replaceAll("ç", "c");
    }

    function apiBase() {
        return "/api/syk-ui";
    }

    function websocketBase() {
        const protocol =
            window.location.protocol === "https:"
                ? "wss"
                : "ws";

        return (
            `${protocol}://`
            + window.location.host
            + "/api/syk-ui"
        );
    }

    async function fetchJson(url) {
        const response = await fetch(
            url,
            {
                headers: {
                    Accept: "application/json",
                },
            }
        );

        if (!response.ok) {
            throw new Error(
                `${response.status} ${response.statusText}`
            );
        }

        return response.json();
    }

    function moduleId(modulePayload) {
        return String(
            modulePayload?.state?.module_id
            ?? modulePayload?.definition?.id
            ?? modulePayload?.definition?.module_id
            ?? modulePayload?.module_id
            ?? modulePayload?.id
            ?? ""
        );
    }

    function moduleTitle(modulePayload) {
        return String(
            modulePayload?.definition?.title
            ?? modulePayload?.definition?.name
            ?? modulePayload?.title
            ?? moduleId(modulePayload)
            ?? "Bilimsel Modül"
        );
    }

    function moduleSearchText(modulePayload) {
        const definition =
            modulePayload?.definition || {};

        return normalize(
            [
                moduleId(modulePayload),
                moduleTitle(modulePayload),
                definition.description,
                definition.category,
                definition.unit,
            ].join(" ")
        );
    }

    async function loadInventory() {
        if (runtimeState.inventoryLoaded) {
            return runtimeState.inventory;
        }

        if (runtimeState.inventoryPromise) {
            return runtimeState.inventoryPromise;
        }

        runtimeState.inventoryPromise =
            fetchJson(
                `${apiBase()}/scientific-modules`
            )
                .then((inventory) => {
                    runtimeState.inventory =
                        Array.isArray(inventory)
                            ? inventory
                            : [];

                    runtimeState.inventoryLoaded = true;

                    return runtimeState.inventory;
                })
                .finally(() => {
                    runtimeState.inventoryPromise = null;
                });

        return runtimeState.inventoryPromise;
    }

    function requestedModuleIds() {
        const focusState =
            window
                .SyKDTSEEvidenceFocus
                ?.getState?.();

        const requested =
            focusState
                ?.payload
                ?.event
                ?.analysis
                ?.requested_modules;

        return Array.isArray(requested)
            ? requested.map(normalize)
            : [];
    }

    function scoreModule(
        modulePayload,
        tabId
    ) {
        const rule = TAB_RULES[tabId];

        if (!rule) {
            return 0;
        }

        const text =
            moduleSearchText(modulePayload);

        const id =
            normalize(moduleId(modulePayload));

        const requested =
            requestedModuleIds();

        let score = 0;

        for (const alias of rule.aliases) {
            const normalizedAlias =
                normalize(alias);

            if (id === normalizedAlias) {
                score += 120;
            }
            else if (
                id.includes(normalizedAlias)
            ) {
                score += 80;
            }
            else if (
                text.includes(normalizedAlias)
            ) {
                score += 45;
            }
        }

        for (const requestedId of requested) {
            if (!requestedId) {
                continue;
            }

            const requestedMatchesTab =
                rule.aliases.some(
                    (alias) => {
                        const normalizedAlias =
                            normalize(alias);

                        return (
                            requestedId
                                === normalizedAlias
                            || requestedId.includes(
                                normalizedAlias
                            )
                            || normalizedAlias.includes(
                                requestedId
                            )
                        );
                    }
                );

            if (!requestedMatchesTab) {
                continue;
            }

            if (id === requestedId) {
                score += 150;
            }
            else if (
                id.includes(requestedId)
                || requestedId.includes(id)
            ) {
                score += 70;
            }
        }

        return score;
    }

    function selectModules(
        inventory,
        tabId
    ) {
        const scored = inventory
            .map((modulePayload) => ({
                modulePayload,
                score: scoreModule(
                    modulePayload,
                    tabId
                ),
            }))
            .filter(
                (item) => item.score > 0
            )
            .sort(
                (left, right) =>
                    right.score - left.score
            );

        const selected = [];
        const usedIds = new Set();

        for (const item of scored) {
            const id = moduleId(
                item.modulePayload
            );

            if (!id || usedIds.has(id)) {
                continue;
            }

            usedIds.add(id);
            selected.push(
                item.modulePayload
            );

            if (selected.length >= 4) {
                break;
            }
        }

        return selected;
    }

    async function fetchModule(
        id
    ) {
        return fetchJson(
            `${apiBase()}/scientific-modules/`
            + encodeURIComponent(id)
        );
    }

    function stateOf(modulePayload) {
        return modulePayload?.state || {};
    }

    function definitionOf(modulePayload) {
        return modulePayload?.definition || {};
    }

    function tabAnalysisTitle(tabId) {
        const titles = {
            surface: "Yüzey Analizi",
            geometry: "Geometri Analizi",
            thermal: "Termal Analiz",
            spectral: "Spektral Analiz",
        };

        return (
            titles[tabId]
            || "Bilimsel Analiz"
        );
    }

    function tabMetricLabel(tabId) {
        const labels = {
            surface: "Doku değişimi",
            geometry: "Geometrik sapma",
            thermal: "Isı farkı",
            spectral: "Spektral sapma",
        };

        return (
            labels[tabId]
            || "Canlı ölçüm"
        );
    }

    function statusLabel(status) {
        const labels = {
            preview: "Ön İzleme",
            verified: "Dijital Doğrulandı",
            analyzing: "Analiz Ediliyor",
            review: "İnceleme Gerekli",
            low_confidence: "Düşük Güven",
            inconsistent: "Tutarsız Veri",
        };

        return (
            labels[status]
            || status
            || "Bilinmiyor"
        );
    }

    function valueText(modulePayload) {
        const state =
            stateOf(modulePayload);

        const definition =
            definitionOf(modulePayload);

        const value =
            state.live_value;

        const unit =
            definition.unit
            ?? definition.primary_unit
            ?? "";

        if (
            value === null
            || value === undefined
            || value === ""
        ) {
            return "Veri bekleniyor";
        }

        return (
            `${escapeHtml(value)}`
            + (
                unit
                    ? ` ${escapeHtml(unit)}`
                    : ""
            )
        );
    }

    function moduleCard(modulePayload) {
        const state =
            stateOf(modulePayload);

        const id =
            moduleId(modulePayload);

        const confidence =
            Number(state.confidence ?? 0);

        return `
            <article
                class="dtse-scientific-live-card"
                data-scientific-module-id="${escapeHtml(
                    id
                )}"
                data-scientific-status="${escapeHtml(
                    state.status
                )}"
                data-scientific-sequence="${escapeHtml(
                    state.sequence
                )}"
            >
                <header>
                    <span>
                        ${escapeHtml(
                            moduleTitle(modulePayload)
                        )}
                    </span>

                    <b>
                        %${confidence.toFixed(1)}
                    </b>
                </header>

                <strong
                    class="dtse-scientific-live-value"
                >
                    ${valueText(modulePayload)}
                </strong>

                <div
                    class="dtse-scientific-live-meta"
                >
                    <span>
                        ${escapeHtml(
                            statusLabel(
                                state.status
                            )
                        )}
                    </span>

                    <code>
                        ${escapeHtml(
                            state.source
                            ?? "kaynak belirtilmedi"
                        )}
                    </code>
                </div>

                <footer>
                    <small>
                        Sıra:
                        ${escapeHtml(
                            state.sequence
                            ?? 0
                        )}
                    </small>

                    <small>
                        ${escapeHtml(
                            state.updated_at
                            ?? "güncelleme bekleniyor"
                        )}
                    </small>
                </footer>
            </article>
        `;
    }

    function panelBody() {
        return document.querySelector(
            "#dtse-focus-tab-body"
        );
    }

    function renderLoading(tabId) {
        const body = panelBody();

        if (!body) {
            return;
        }

        const title =
            TAB_RULES[tabId]?.fallbackTitle
            ?? "Bilimsel Analiz";

        body.innerHTML = `
            <section
                class="dtse-scientific-runtime-view"
                data-runtime-tab="${escapeHtml(
                    tabId
                )}"
                data-tab-content="${escapeHtml(
                    tabId
                )}"
                data-loading="true"
            >
                <header>
                    <div>
                        <span>
                            CANLI BİLİMSEL RUNTIME
                        </span>

                        <strong>
                            ${escapeHtml(title)}
                        </strong>

                        <span
                            class="dtse-scientific-analysis-title"
                        >
                            ${escapeHtml(
                                tabAnalysisTitle(tabId)
                            )}
                        </span>
                    </div>

                    <b>
                        Modüller bağlanıyor…
                    </b>
                </header>

                <div
                    class="dtse-scientific-runtime-loading"
                >
                    Bilimsel veriler alınıyor.
                </div>
            </section>
        `;
    }

    function renderError(
        tabId,
        error
    ) {
        const body = panelBody();

        if (!body) {
            return;
        }

        body.innerHTML = `
            <section
                class="dtse-scientific-runtime-view"
                data-runtime-tab="${escapeHtml(
                    tabId
                )}"
                data-tab-content="${escapeHtml(
                    tabId
                )}"
                data-error="true"
            >
                <header>
                    <div>
                        <span>
                            CANLI BİLİMSEL RUNTIME
                        </span>

                        <strong>
                            Veri bağlantısı kurulamadı
                        </strong>
                    </div>
                </header>

                <div
                    class="dtse-scientific-runtime-error"
                >
                    ${escapeHtml(
                        error?.message
                        ?? error
                    )}
                </div>
            </section>
        `;
    }

    function renderModules(tabId) {
        const body = panelBody();

        if (!body) {
            return;
        }

        const modules =
            runtimeState.selectedModules
                .map((selected) => {
                    const id =
                        moduleId(selected);

                    return (
                        runtimeState
                            .modulePayloads
                            .get(id)
                        || selected
                    );
                });

        const title =
            TAB_RULES[tabId]?.fallbackTitle
            ?? "Bilimsel Analiz";

        body.innerHTML = `
            <section
                class="dtse-scientific-runtime-view"
                data-runtime-tab="${escapeHtml(
                    tabId
                )}"
                data-tab-content="${escapeHtml(
                    tabId
                )}"
                data-module-count="${modules.length}"
            >
                <header>
                    <div>
                        <span>
                            CANLI BİLİMSEL RUNTIME
                        </span>

                        <strong>
                            ${escapeHtml(title)}
                        </strong>

                        <span
                            class="dtse-scientific-analysis-title"
                        >
                            ${escapeHtml(
                                tabAnalysisTitle(tabId)
                            )}
                        </span>
                    </div>

                    <b>
                        ${modules.length}
                        modül bağlı
                    </b>
                </header>

                <div
                    class="dtse-scientific-metric-label"
                >
                    ${escapeHtml(
                        tabMetricLabel(tabId)
                    )}
                </div>

                <div
                    class="dtse-scientific-live-grid"
                >
                    ${modules
                        .map(moduleCard)
                        .join("")}
                </div>

                <footer
                    class="dtse-scientific-runtime-footer"
                >
                    <span>
                        WebSocket canlı güncelleme açık
                    </span>

                    <small>
                        Bu sonuçlar dijital ortamla
                        sınırlıdır; saha doğrulaması
                        gereklidir.
                    </small>
                </footer>
            </section>
        `;

        runtimeState.renderSequence += 1;

        document.dispatchEvent(
            new CustomEvent(
                "syk:dtse-scientific-runtime-rendered",
                {
                    detail: {
                        tabId,
                        moduleCount:
                            modules.length,
                        sequence:
                            runtimeState
                                .renderSequence,
                    },
                }
            )
        );
    }

    function closeSockets() {
        for (
            const socket
            of runtimeState
                .activeSockets
                .values()
        ) {
            try {
                socket.close();
            }
            catch {
                // Kapanmış bağlantı.
            }
        }

        runtimeState.activeSockets.clear();
    }

    function connectModuleSocket(id) {
        if (
            runtimeState
                .activeSockets
                .has(id)
        ) {
            return;
        }

        const url =
            `${websocketBase()}`
            + `/scientific-modules/`
            + `${encodeURIComponent(id)}`
            + "/live";

        const socket =
            new WebSocket(url);

        runtimeState
            .activeSockets
            .set(id, socket);

        socket.addEventListener(
            "message",
            (message) => {
                try {
                    const payload =
                        JSON.parse(
                            message.data
                        );

                    const currentPayload =
                        runtimeState
                            .modulePayloads
                            .get(id);

                    const currentSequence =
                        Number(
                            currentPayload
                                ?.state
                                ?.sequence
                            ?? -1
                        );

                    const incomingSequence =
                        Number(
                            payload
                                ?.state
                                ?.sequence
                            ?? -1
                        );

                    if (
                        incomingSequence
                        <= currentSequence
                    ) {
                        return;
                    }

                    runtimeState
                        .modulePayloads
                        .set(id, payload);

                    if (
                        runtimeState.activeTab
                    ) {
                        renderModules(
                            runtimeState
                                .activeTab
                        );
                    }
                }
                catch {
                    return;
                }
            }
        );

        socket.addEventListener(
            "close",
            () => {
                runtimeState
                    .activeSockets
                    .delete(id);
            }
        );
    }

    async function activateTab(tabId) {
        if (!TAB_RULES[tabId]) {
            return;
        }

        runtimeState.activeTab =
            tabId;

        closeSockets();
        renderLoading(tabId);

        try {
            const inventory =
                await loadInventory();

            const selected =
                selectModules(
                    inventory,
                    tabId
                );

            runtimeState.selectedModules =
                selected;

            runtimeState.modulePayloads.clear();

            const detailed =
                await Promise.all(
                    selected.map(
                        async (
                            modulePayload
                        ) => {
                            const id =
                                moduleId(
                                    modulePayload
                                );

                            if (!id) {
                                return modulePayload;
                            }

                            try {
                                return await fetchModule(
                                    id
                                );
                            }
                            catch {
                                return modulePayload;
                            }
                        }
                    )
                );

            runtimeState.selectedModules =
                detailed;

            for (
                const modulePayload
                of detailed
            ) {
                const id =
                    moduleId(modulePayload);

                if (!id) {
                    continue;
                }

                runtimeState
                    .modulePayloads
                    .set(
                        id,
                        modulePayload
                    );

                connectModuleSocket(id);
            }

            renderModules(tabId);
        }
        catch (error) {
            renderError(
                tabId,
                error
            );
        }
    }

    document.addEventListener(
        "syk:dtse-evidence-focused",
        () => {
            activateTab("surface");
        }
    );

    document.addEventListener(
        "syk:dtse-focus-tab-changed",
        (event) => {
            activateTab(
                event.detail?.tabId
            );
        }
    );

    document.addEventListener(
        "syk:dtse-evidence-focus-closed",
        () => {
            closeSockets();

            runtimeState.activeTab =
                null;

            runtimeState
                .selectedModules = [];

            runtimeState
                .modulePayloads
                .clear();
        }
    );

    window.SyKDTSEScientificRuntime = {
        activateTab,
        loadInventory,
        closeSockets,

        getState: () => ({
            activeTab:
                runtimeState.activeTab,

            inventoryLoaded:
                runtimeState
                    .inventoryLoaded,

            moduleCount:
                runtimeState
                    .selectedModules
                    .length,

            socketCount:
                runtimeState
                    .activeSockets
                    .size,

            renderSequence:
                runtimeState
                    .renderSequence,
        }),
    };
})();