(() => {
    "use strict";

    const state = {
        active: false,
        selectedTab: "surface",
        payload: null,
        originalTransform: "",
        originalTransformOrigin: "",
    };

    const TAB_DEFINITIONS = {
        surface: {
            title: "Yüzey",
            modules: [
                "DTSE yüzey modeli",
                "Doku değişimi",
                "Pürüzlülük",
                "Aşınma",
            ],
        },
        geometry: {
            title: "Geometri",
            modules: [
                "Oyuk",
                "Kanal",
                "Çatlak",
                "Eğim",
                "Ölçüm",
            ],
        },
        thermal: {
            title: "Termal",
            modules: [
                "Isı farkı",
                "Termal sapma",
                "Sıcaklık dağılımı",
            ],
        },
        spectral: {
            title: "Spektral",
            modules: [
                "Renk değişimi",
                "Yansıma",
                "Spektral sapma",
                "Materyal adayı",
            ],
        },
    };

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function getStage() {
        return (
            document.querySelector(
                "[data-dtse-media-stage]"
            )
            || document.querySelector(
                "#module-view"
            )
            || document.querySelector(
                "main"
            )
        );
    }

    function ensurePanel() {
        let panel = document.querySelector(
            "#dtse-evidence-focus-panel"
        );

        if (panel) {
            return panel;
        }

        panel = document.createElement("section");
        panel.id = "dtse-evidence-focus-panel";
        panel.className =
            "dtse-evidence-focus-panel";
        panel.hidden = true;

        document.body.appendChild(panel);

        return panel;
    }

    function ensureFocusFrame(stage) {
        let frame = stage.querySelector(
            ".dtse-evidence-focus-frame"
        );

        if (frame) {
            return frame;
        }

        frame = document.createElement("div");
        frame.className =
            "dtse-evidence-focus-frame";

        frame.innerHTML = `
            <span class="dtse-focus-corner top-left"></span>
            <span class="dtse-focus-corner top-right"></span>
            <span class="dtse-focus-corner bottom-left"></span>
            <span class="dtse-focus-corner bottom-right"></span>
        `;

        stage.appendChild(frame);

        return frame;
    }

    function focusStage(event) {
        const stage = getStage();

        if (!stage) {
            throw new Error(
                "DTSE görüntü alanı bulunamadı."
            );
        }

        const box =
            event.visual_layer?.box || {};

        const x = Number(box.x ?? 0);
        const y = Number(box.y ?? 0);
        const width = Math.max(
            0.01,
            Number(box.width ?? 1)
        );
        const height = Math.max(
            0.01,
            Number(box.height ?? 1)
        );

        const centerX =
            Math.min(
                1,
                Math.max(
                    0,
                    x + width / 2
                )
            );

        const centerY =
            Math.min(
                1,
                Math.max(
                    0,
                    y + height / 2
                )
            );

        const zoom = Math.min(
            3.4,
            Math.max(
                1.15,
                0.78 / Math.max(
                    width,
                    height
                )
            )
        );

        if (!state.active) {
            state.originalTransform =
                stage.style.transform || "";

            state.originalTransformOrigin =
                stage.style.transformOrigin || "";
        }

        stage.classList.add(
            "dtse-evidence-stage-focused"
        );

        stage.style.transformOrigin =
            `${centerX * 100}% ${centerY * 100}%`;

        stage.style.transform =
            `scale(${zoom.toFixed(3)})`;

        const frame =
            ensureFocusFrame(stage);

        frame.style.left =
            `${x * 100}%`;

        frame.style.top =
            `${y * 100}%`;

        frame.style.width =
            `${width * 100}%`;

        frame.style.height =
            `${height * 100}%`;

        frame.hidden = false;

        stage.dataset.dtseFocusEventId =
            event.id;

        stage.dataset.dtseFocusZoom =
            zoom.toFixed(3);
    }

    function releaseStage() {
        const stage = getStage();

        if (!stage) {
            return;
        }

        stage.classList.remove(
            "dtse-evidence-stage-focused"
        );

        stage.style.transform =
            state.originalTransform;

        stage.style.transformOrigin =
            state.originalTransformOrigin;

        delete stage.dataset.dtseFocusEventId;
        delete stage.dataset.dtseFocusZoom;

        const frame = stage.querySelector(
            ".dtse-evidence-focus-frame"
        );

        if (frame) {
            frame.hidden = true;
        }
    }

    function renderTabContent(
        event,
        tabId
    ) {
        const definition =
            TAB_DEFINITIONS[tabId];

        const confidence =
            Number(
                event.signal?.confidence
                ?? event.syframe?.confidence
                ?? 0
            );

        const requestedModules =
            event.analysis?.requested_modules
            || [];

        return `
            <div
                class="dtse-focus-tab-content"
                data-tab-content="${escapeHtml(
                    tabId
                )}"
            >
                <header>
                    <div>
                        <span>
                            ${escapeHtml(
                                definition.title
                            )} İncelemesi
                        </span>

                        <strong>
                            ${escapeHtml(
                                event.signal?.label
                            )}
                        </strong>
                    </div>

                    <b>
                        Dijital güven
                        %${confidence.toFixed(1)}
                    </b>
                </header>

                <div class="dtse-focus-analysis-grid">
                    ${definition.modules
                        .map(
                            (moduleName) => `
                                <article>
                                    <span>
                                        ${escapeHtml(
                                            moduleName
                                        )}
                                    </span>

                                    <strong>
                                        İnceleme kuyruğunda
                                    </strong>
                                </article>
                            `
                        )
                        .join("")}
                </div>

                <div class="dtse-focus-requested-modules">
                    <span>
                        Çağrılan analiz birimleri
                    </span>

                    <code>
                        ${
                            requestedModules.length
                                ? requestedModules
                                    .map(escapeHtml)
                                    .join(" · ")
                                : "DTSE ortak analiz"
                        }
                    </code>
                </div>

                <small>
                    Bu ekran dijital inceleme
                    katmanıdır; saha doğrulaması
                    gereklidir.
                </small>
            </div>
        `;
    }

    function renderPanel(event) {
        const panel = ensurePanel();

        const tabs = Object.entries(
            TAB_DEFINITIONS
        )
            .map(
                ([tabId, definition]) => `
                    <button
                        type="button"
                        data-dtse-focus-tab="${escapeHtml(
                            tabId
                        )}"
                        aria-selected="${
                            tabId
                            === state.selectedTab
                        }"
                    >
                        ${escapeHtml(
                            definition.title
                        )}
                    </button>
                `
            )
            .join("");

        panel.innerHTML = `
            <header
                class="dtse-focus-panel-header"
            >
                <div>
                    <span>
                        DTSE ODAKLI İNCELEME
                    </span>

                    <strong>
                        ${escapeHtml(
                            event.signal?.label
                        )}
                    </strong>
                </div>

                <button
                    type="button"
                    id="dtse-evidence-focus-close"
                    aria-label="Odaklı incelemeyi kapat"
                >
                    ×
                </button>
            </header>

            <nav
                class="dtse-focus-tabs"
                aria-label="DTSE inceleme katmanları"
            >
                ${tabs}
            </nav>

            <div
                id="dtse-focus-tab-body"
            >
                ${renderTabContent(
                    event,
                    state.selectedTab
                )}
            </div>
        `;

        panel.hidden = false;

        panel.querySelectorAll(
            "[data-dtse-focus-tab]"
        ).forEach((button) => {
            button.addEventListener(
                "click",
                () => {
                    selectTab(
                        button.dataset
                            .dtseFocusTab
                    );
                }
            );
        });

        panel.querySelector(
            "#dtse-evidence-focus-close"
        ).addEventListener(
            "click",
            close
        );
    }

    function selectTab(tabId) {
        if (!TAB_DEFINITIONS[tabId]) {
            throw new Error(
                `Bilinmeyen DTSE sekmesi: ${tabId}`
            );
        }

        state.selectedTab = tabId;

        const panel = ensurePanel();

        panel.querySelectorAll(
            "[data-dtse-focus-tab]"
        ).forEach((button) => {
            button.setAttribute(
                "aria-selected",
                String(
                    button.dataset
                        .dtseFocusTab
                    === tabId
                )
            );
        });

        const body = panel.querySelector(
            "#dtse-focus-tab-body"
        );

        if (
            body
            && state.payload?.event
        ) {
            body.innerHTML =
                renderTabContent(
                    state.payload.event,
                    tabId
                );
        }

        document.dispatchEvent(
            new CustomEvent(
                "syk:dtse-focus-tab-changed",
                {
                    detail: {
                        tabId,
                        payload:
                            state.payload,
                    },
                }
            )
        );
    }

    function open(payload = null) {
        const resolvedPayload =
            payload
            || window
                .SyKDTSEEvidenceCard
                ?.getLatest?.();

        const event =
            resolvedPayload?.event;

        if (!event) {
            throw new Error(
                "Odaklanacak DTSE kanıt olayı bulunamadı."
            );
        }

        state.payload =
            resolvedPayload;

        state.active = true;
        state.selectedTab = "surface";

        focusStage(event);
        renderPanel(event);

        document.body.classList.add(
            "dtse-evidence-focus-active"
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:dtse-evidence-focused",
                {
                    detail:
                        resolvedPayload,
                }
            )
        );
    }

    function close() {
        releaseStage();

        const panel = ensurePanel();
        panel.hidden = true;

        state.active = false;

        document.body.classList.remove(
            "dtse-evidence-focus-active"
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:dtse-evidence-focus-closed"
            )
        );
    }

    function bindEvidenceCard() {
        document.addEventListener(
            "click",
            (event) => {
                const card =
                    event.target.closest(
                        ".dtse-evidence-card"
                    );

                if (!card) {
                    return;
                }

                open();
            }
        );
    }

    window.SyKDTSEEvidenceFocus = {
        open,
        close,
        selectTab,
        getState: () => ({
            active: state.active,
            selectedTab:
                state.selectedTab,
            payload:
                state.payload,
        }),
    };

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            ensurePanel();
            bindEvidenceCard();
        }
    );
})();