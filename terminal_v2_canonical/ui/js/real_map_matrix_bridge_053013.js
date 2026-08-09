(() => {
    "use strict";

    const STATE_URL =
        "/api/v2/map/state";

    const SELECTION_URL =
        "/api/v2/map/selection";

    const VIEWPORT_URL =
        "/api/v2/map/viewport";

    const MODE_URL =
        "/api/v2/map/mode";

    let lastSelectionSignature = "";
    let lastStateSignature = "";
    let syncTimer = null;

    const q = (selector, root=document) =>
        root.querySelector(selector);

    const qa = (selector, root=document) =>
        [...root.querySelectorAll(selector)];

    function slug(value) {
        const map = {
            "ç":"c",
            "ğ":"g",
            "ı":"i",
            "ö":"o",
            "ş":"s",
            "ü":"u"
        };

        return String(value || "")
            .toLocaleLowerCase("tr-TR")
            .split("")
            .map(char => map[char] || char)
            .join("")
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    function getSelectedLayers() {
        const rows = [];

        qa(".syk009-secim.secili")
            .forEach(node => {
                const title =
                    (
                        node.querySelector(
                            "span:nth-of-type(2)"
                        )?.textContent
                        ||
                        node.textContent
                        ||
                        ""
                    )
                    .replace("›", "")
                    .trim();

                if (!title) {
                    return;
                }

                rows.push({
                    id:
                        node.dataset.katmanId
                        || slug(title),

                    title,

                    category:
                        node.dataset.category
                        || "dinamik",

                    priority:
                        Number(
                            node.dataset.oncelik
                            || 50
                        ),

                    heavy:
                        node.dataset.heavy === "1"
                });
            });

        return rows;
    }

    async function jsonFetch(url, options={}) {
        const response =
            await fetch(
                url,
                {
                    cache:
                        "no-store",

                    headers: {
                        "Content-Type":
                            "application/json",
                        ...(options.headers || {})
                    },

                    ...options
                }
            );

        if (!response.ok) {
            throw new Error(
                `HTTP_${response.status}_${url}`
            );
        }

        return response.json();
    }

    async function syncSelection() {
        const selected =
            getSelectedLayers();

        const signature =
            JSON.stringify(
                selected.map(
                    item => [
                        item.id,
                        item.priority,
                        item.heavy
                    ]
                )
            );

        if (
            signature ===
            lastSelectionSignature
        ) {
            return;
        }

        lastSelectionSignature =
            signature;

        const state =
            await jsonFetch(
                SELECTION_URL,
                {
                    method:
                        "POST",

                    body:
                        JSON.stringify({
                            selected
                        })
                }
            );

        renderRealMatrix(state);
    }

    function ensureRealMatrixSurface() {
        const grid =
            q("#syk010SideGrid");

        if (!grid) {
            return null;
        }

        grid.dataset.source =
            "real-map-engine";

        return grid;
    }

    function hideRightIfEmpty(state) {
        const workspace =
            q("#syk010Workspace");

        const right =
            q("#syk010SagBolum");

        const layers =
            state?.active_layers
            || [];

        if (!workspace || !right) {
            return;
        }

        if (layers.length === 0) {
            right.classList.add(
                "syk011-sag-gizli"
            );

            workspace.classList.remove(
                "syk011-sag-aktif"
            );

            workspace.classList.add(
                "syk011-sadece-harita"
            );

            return;
        }

        right.classList.remove(
            "syk011-sag-gizli"
        );

        workspace.classList.remove(
            "syk011-sadece-harita"
        );

        workspace.classList.add(
            "syk011-sag-aktif"
        );
    }

    function rendererContent(layer, index) {
        const renderer =
            layer.payload?.renderer
            || "generic";

        const title =
            layer.title;

        if (renderer === "map-overlay") {
            return `
                <div class="syk013-render syk013-map-render">
                    <div class="syk013-grid-lines"></div>
                    <span class="syk013-watermark">
                        ${index + 1}
                    </span>
                    <strong>${title}</strong>
                    <small>Harita katmanı canlı</small>
                </div>
            `;
        }

        if (renderer === "image-video") {
            return `
                <div class="syk013-render syk013-media-render">
                    <span class="syk013-pulse"></span>
                    <strong>${title}</strong>
                    <small>Görüntü akışı hazır</small>
                </div>
            `;
        }

        if (
            renderer === "analysis"
            ||
            renderer === "evidence"
        ) {
            return `
                <div class="syk013-render syk013-analysis-render">
                    <svg
                        viewBox="0 0 300 100"
                        preserveAspectRatio="none"
                        aria-hidden="true"
                    >
                        <polyline
                            points="0,72 40,48 78,60 120,28 162,54 210,21 300,41"
                        />
                    </svg>

                    <strong>${title}</strong>
                    <small>Canlı analiz katmanı</small>
                </div>
            `;
        }

        return `
            <div class="syk013-render syk013-generic-render">
                <span class="syk013-watermark">
                    ${index + 1}
                </span>
                <strong>${title}</strong>
                <small>${layer.category}</small>
            </div>
        `;
    }

    function renderRealMatrix(state) {
        const grid =
            ensureRealMatrixSurface();

        if (!grid) {
            return;
        }

        hideRightIfEmpty(state);

        const layers =
            state?.active_layers
            || [];

        grid.innerHTML =
            "";

        grid.dataset.adet =
            String(layers.length);

        layers.forEach(
            (layer,index) => {
                const card =
                    document.createElement(
                        "button"
                    );

                card.type =
                    "button";

                card.className =
                    "syk011-matris-karti syk013-real-card";

                card.dataset.kartId =
                    layer.id;

                card.dataset.renderer =
                    layer.payload?.renderer
                    || "generic";

                card.innerHTML =
                    rendererContent(
                        layer,
                        index
                    );

                card.addEventListener(
                    "click",
                    () => {
                        const active =
                            card.classList.contains(
                                "syk013-odak"
                            );

                        qa(
                            ".syk013-real-card",
                            grid
                        ).forEach(
                            item => {
                                item.classList.remove(
                                    "syk013-odak",
                                    "syk013-odak-disi"
                                );
                            }
                        );

                        grid.classList.remove(
                            "syk013-tek-odak"
                        );

                        if (active) {
                            return;
                        }

                        grid.classList.add(
                            "syk013-tek-odak"
                        );

                        qa(
                            ".syk013-real-card",
                            grid
                        ).forEach(
                            item => {
                                if (item === card) {
                                    item.classList.add(
                                        "syk013-odak"
                                    );
                                }
                                else {
                                    item.classList.add(
                                        "syk013-odak-disi"
                                    );
                                }
                            }
                        );
                    }
                );

                grid.appendChild(
                    card
                );
            }
        );

        const count =
            q("#syk009SecimDurumu");

        if (count) {
            count.textContent =
                `${layers.length} gerçek katman etkin`;
        }

        document.documentElement.dataset
            .realMatrixCount =
            String(layers.length);
    }

    async function pullState() {
        const state =
            await jsonFetch(
                STATE_URL
            );

        const signature =
            JSON.stringify(
                state
            );

        if (
            signature ===
            lastStateSignature
        ) {
            return;
        }

        lastStateSignature =
            signature;

        renderRealMatrix(
            state
        );
    }

    async function syncViewportFromGPS() {
        if (
            !navigator.geolocation
        ) {
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async position => {
                try {
                    await jsonFetch(
                        VIEWPORT_URL,
                        {
                            method:
                                "POST",

                            body:
                                JSON.stringify({
                                    latitude:
                                        position.coords.latitude,

                                    longitude:
                                        position.coords.longitude,

                                    zoom:
                                        12
                                })
                        }
                    );
                }
                catch(error) {
                    console.warn(
                        "GPS_VIEWPORT_SYNC_FAIL",
                        error
                    );
                }
            },
            () => {},
            {
                enableHighAccuracy:
                    false,

                maximumAge:
                    60000,

                timeout:
                    3000
            }
        );
    }

    function bindMapModes() {
        qa(
            '.calisma-paneli[data-panel="harita"] [data-gorunum-009]'
        ).forEach(
            button => {
                button.addEventListener(
                    "click",
                    async () => {
                        const raw =
                            (
                                button.dataset.gorunum009
                                || ""
                            )
                            .toLocaleLowerCase(
                                "tr-TR"
                            );

                        const map = {
                            "2b":
                                "harita",
                            "3b":
                                "arazi",
                            "ar":
                                "topografya"
                        };

                        const mode =
                            map[raw];

                        if (!mode) {
                            return;
                        }

                        try {
                            await jsonFetch(
                                MODE_URL,
                                {
                                    method:
                                        "POST",

                                    body:
                                        JSON.stringify({
                                            mode
                                        })
                                }
                            );

                            await pullState();
                        }
                        catch(error) {
                            console.error(
                                "MAP_MODE_SYNC_FAIL",
                                error
                            );
                        }
                    }
                );
            }
        );
    }

    function observeDrawer() {
        const drawer =
            q("#syk009Drawer");

        if (!drawer) {
            return;
        }

        const observer =
            new MutationObserver(
                () => {
                    clearTimeout(
                        syncTimer
                    );

                    syncTimer =
                        setTimeout(
                            () => {
                                syncSelection()
                                    .catch(
                                        error =>
                                            console.error(
                                                "LAYER_SELECTION_SYNC_FAIL",
                                                error
                                            )
                                    );
                            },
                            80
                        );
                }
            );

        observer.observe(
            drawer,
            {
                subtree:
                    true,

                childList:
                    true,

                attributes:
                    true,

                attributeFilter:
                    ["class"]
            }
        );
    }

    async function start() {
        observeDrawer();

        bindMapModes();

        await syncSelection();

        await pullState();

        syncViewportFromGPS();

        /*
         * Anlık canlı durum:
         * yeni motor işlemleri sağ matrise kısa aralıkla yansır.
         */
        setInterval(
            () => {
                pullState()
                    .catch(
                        error =>
                            console.warn(
                                "MAP_STATE_POLL_FAIL",
                                error
                            )
                    );
            },
            1000
        );

        document.documentElement.dataset
            .syk013Runtime =
            "ready";

        console.info(
            "SPRINT_053_013_REAL_MATRIX_READY"
        );
    }

    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            () => {
                setTimeout(
                    () => {
                        start().catch(
                            error =>
                                console.error(
                                    "SPRINT_053_013_START_FAIL",
                                    error
                                )
                        );
                    },
                    800
                );
            }
        );
    }
    else {
        setTimeout(
            () => {
                start().catch(
                    error =>
                        console.error(
                            "SPRINT_053_013_START_FAIL",
                            error
                        )
                );
            },
            800
        );
    }
})();
