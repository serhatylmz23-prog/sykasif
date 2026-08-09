(() => {
    "use strict";

    const STATE_URL = "/api/v2/map/state";
    const MODE_URL = "/api/v2/map/mode";
    const VIEWPORT_URL = "/api/v2/map/viewport";

    const TILE_PROVIDERS = {

        harita: {
            url:
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution:
                "&copy; OpenStreetMap katkıda bulunanlar",
            maxZoom:
                19
        },

        uydu: {
            url:
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution:
                "Esri World Imagery",
            maxZoom:
                19
        },

        arazi: {
            url:
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
            attribution:
                "Esri Terrain",
            maxZoom:
                13
        },

        topografya: {
            url:
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            attribution:
                "Esri World Topographic Map",
            maxZoom:
                19
        }
    };

    let map = null;
    let activeTile = null;
    let activeMode = null;
    let gpsMarker = null;
    let lastViewport = null;
    let resizeObserver = null;

    const q = (selector, root=document) =>
        root.querySelector(selector);

    function ensureLeafletCss() {

        if (
            document.querySelector(
                'link[data-syk-leaflet]'
            )
        ) {
            return;
        }

        const link =
            document.createElement("link");

        link.rel =
            "stylesheet";

        link.href =
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";

        link.dataset.sykLeaflet =
            "1";

        document.head.appendChild(
            link
        );
    }

    function loadLeaflet() {

        if (window.L) {
            return Promise.resolve(
                window.L
            );
        }

        ensureLeafletCss();

        return new Promise(
            (resolve,reject) => {

                const existing =
                    document.querySelector(
                        'script[data-syk-leaflet]'
                    );

                if (existing) {

                    existing.addEventListener(
                        "load",
                        () => resolve(window.L),
                        {
                            once:
                                true
                        }
                    );

                    existing.addEventListener(
                        "error",
                        reject,
                        {
                            once:
                                true
                        }
                    );

                    return;
                }

                const script =
                    document.createElement(
                        "script"
                    );

                script.src =
                    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

                script.defer =
                    true;

                script.dataset.sykLeaflet =
                    "1";

                script.addEventListener(
                    "load",
                    () => resolve(window.L),
                    {
                        once:
                            true
                    }
                );

                script.addEventListener(
                    "error",
                    () => reject(
                        new Error(
                            "LEAFLET_YUKLENEMEDI"
                        )
                    ),
                    {
                        once:
                            true
                    }
                );

                document.head.appendChild(
                    script
                );
            }
        );
    }

    async function fetchJson(
        url,
        options={}
    ) {

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

    function findMapPanel() {

        return q(
            '.calisma-paneli[data-panel="harita"]'
        );
    }

    function removePlaceholder() {

        const panel =
            findMapPanel();

        if (!panel) {
            return;
        }

        /*
         * Eski çizgi/placeholder içeriklerini
         * tamamen görünmez hale getiriyoruz.
         */

        [
            ".harita-yuzeyi",
            ".map-placeholder",
            ".rota-placeholder",
            ".route-preview",
            ".harita-placeholder"
        ]
        .forEach(
            selector => {

                panel
                    .querySelectorAll(
                        selector
                    )
                    .forEach(
                        node => {

                            if (
                                node.id ===
                                "syk013aRealMap"
                            ) {
                                return;
                            }

                            node.classList.add(
                                "syk013a-placeholder-gizli"
                            );
                        }
                    );
            }
        );
    }

    function ensureMapSurface() {

        const panel =
            findMapPanel();

        if (!panel) {
            throw new Error(
                "HARITA_PANELI_BULUNAMADI"
            );
        }

        let surface =
            q(
                "#syk013aRealMap",
                panel
            );

        if (surface) {
            return surface;
        }

        surface =
            document.createElement(
                "div"
            );

        surface.id =
            "syk013aRealMap";

        surface.className =
            "syk013a-real-map";

        panel.appendChild(
            surface
        );

        return surface;
    }

    function createMap(
        L,
        state
    ) {

        const surface =
            ensureMapSurface();

        if (map) {
            return map;
        }

        const viewport =
            state.viewport || {};

        const latitude =
            Number(
                viewport.latitude
                ?? 39.0
            );

        const longitude =
            Number(
                viewport.longitude
                ?? 35.0
            );

        const zoom =
            Number(
                viewport.zoom
                ?? 6
            );

        map =
            L.map(
                surface,
                {
                    zoomControl:
                        false,

                    attributionControl:
                        true,

                    preferCanvas:
                        true,

                    worldCopyJump:
                        true
                }
            );

        map.setView(
            [
                latitude,
                longitude
            ],
            zoom
        );

        /*
         * Minimal zoom kontrolü.
         */

        L.control
            .zoom({
                position:
                    "bottomright"
            })
            .addTo(
                map
            );

        lastViewport = {
            latitude,
            longitude,
            zoom
        };

        installResizeObserver();

        return map;
    }

    function installResizeObserver() {

        if (
            resizeObserver ||
            !map
        ) {
            return;
        }

        const panel =
            findMapPanel();

        if (!panel) {
            return;
        }

        resizeObserver =
            new ResizeObserver(
                () => {
                    requestAnimationFrame(
                        () => {
                            map?.invalidateSize(
                                false
                            );
                        }
                    );
                }
            );

        resizeObserver.observe(
            panel
        );
    }

    function setBaseLayer(
        L,
        mode
    ) {

        const provider =
            TILE_PROVIDERS[
                mode
            ]
            ||
            TILE_PROVIDERS.harita;

        if (
            activeTile &&
            activeMode === mode
        ) {
            return;
        }

        if (activeTile) {

            map.removeLayer(
                activeTile
            );

            activeTile =
                null;
        }

        activeTile =
            L.tileLayer(
                provider.url,
                {
                    attribution:
                        provider.attribution,

                    maxZoom:
                        provider.maxZoom,

                    updateWhenIdle:
                        true,

                    keepBuffer:
                        3,

                    crossOrigin:
                        true
                }
            );

        activeTile.addTo(
            map
        );

        activeMode =
            mode;

        document.documentElement
            .dataset.sykMapMode =
            mode;
    }

    function syncViewport(
        state
    ) {

        if (!map) {
            return;
        }

        const viewport =
            state.viewport || {};

        const latitude =
            Number(
                viewport.latitude
            );

        const longitude =
            Number(
                viewport.longitude
            );

        const zoom =
            Number(
                viewport.zoom
            );

        if (
            !Number.isFinite(
                latitude
            )
            ||
            !Number.isFinite(
                longitude
            )
        ) {
            return;
        }

        const changed =
            !lastViewport
            ||
            Math.abs(
                lastViewport.latitude -
                latitude
            ) > 0.000001
            ||
            Math.abs(
                lastViewport.longitude -
                longitude
            ) > 0.000001
            ||
            (
                Number.isFinite(zoom)
                &&
                lastViewport.zoom !== zoom
            );

        if (!changed) {
            return;
        }

        map.setView(
            [
                latitude,
                longitude
            ],
            Number.isFinite(zoom)
                ? zoom
                : map.getZoom(),
            {
                animate:
                    true
            }
        );

        lastViewport = {
            latitude,
            longitude,
            zoom:
                Number.isFinite(zoom)
                    ? zoom
                    : map.getZoom()
        };
    }

    function updateGpsMarker(
        L,
        latitude,
        longitude
    ) {

        if (!map) {
            return;
        }

        const latlng =
            [
                latitude,
                longitude
            ];

        if (!gpsMarker) {

            gpsMarker =
                L.circleMarker(
                    latlng,
                    {
                        radius:
                            7,

                        weight:
                            2,

                        opacity:
                            1,

                        fillOpacity:
                            0.72
                    }
                )
                .addTo(
                    map
                );

            gpsMarker.bindTooltip(
                "Mevcut konum",
                {
                    direction:
                        "top"
                }
            );
        }
        else {

            gpsMarker.setLatLng(
                latlng
            );
        }
    }

    function requestGps(
        L
    ) {

        if (
            !navigator.geolocation
        ) {
            return;
        }

        navigator
            .geolocation
            .getCurrentPosition(
                async position => {

                    const latitude =
                        position.coords.latitude;

                    const longitude =
                        position.coords.longitude;

                    updateGpsMarker(
                        L,
                        latitude,
                        longitude
                    );

                    try {

                        const state =
                            await fetchJson(
                                VIEWPORT_URL,
                                {
                                    method:
                                        "POST",

                                    body:
                                        JSON.stringify({
                                            latitude,
                                            longitude,
                                            zoom:
                                                Math.max(
                                                    map?.getZoom()
                                                    || 12,
                                                    12
                                                )
                                        })
                                }
                            );

                        syncViewport(
                            state
                        );
                    }
                    catch(error) {

                        console.warn(
                            "GPS_BACKEND_SYNC_FAIL",
                            error
                        );
                    }
                },
                error => {

                    console.info(
                        "GPS_KULLANILMADI",
                        error.code
                    );
                },
                {
                    enableHighAccuracy:
                        false,

                    timeout:
                        5000,

                    maximumAge:
                        60000
                }
            );
    }

    function modeButtonText(
        button
    ) {

        return String(
            button.textContent
            || ""
        )
        .trim()
        .toLocaleLowerCase(
            "tr-TR"
        );
    }

    function bindModeControls(
        L
    ) {

        const panel =
            findMapPanel();

        if (!panel) {
            return;
        }

        const buttons =
            [
                ...panel.querySelectorAll(
                    ".syk009-panel-araclari button"
                )
            ];

        buttons.forEach(
            button => {

                if (
                    button.dataset
                        .syk013aBound ===
                    "1"
                ) {
                    return;
                }

                const label =
                    modeButtonText(
                        button
                    );

                let mode =
                    null;

                if (label === "2b") {
                    mode =
                        "harita";
                }
                else if (
                    label === "3b"
                ) {
                    /*
                     * 3B arazi tabanı.
                     * Gerçek 3D terrain sonraki motor.
                     */
                    mode =
                        "arazi";
                }
                else if (
                    label === "ar"
                ) {
                    /*
                     * AR modunda taban harita
                     * topografik kalır.
                     * Kamera/AR kompozit katmanı
                     * sonraki zincirde bağlanacak.
                     */
                    mode =
                        "topografya";
                }

                if (!mode) {
                    return;
                }

                button.dataset
                    .syk013aBound =
                    "1";

                button.addEventListener(
                    "click",
                    async () => {

                        try {

                            const state =
                                await fetchJson(
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

                            setBaseLayer(
                                L,
                                state.viewport.mode
                            );
                        }
                        catch(error) {

                            console.error(
                                "MAP_MODE_CHANGE_FAIL",
                                error
                            );
                        }
                    }
                );
            }
        );
    }

    function createBasemapSelector(
        L
    ) {

        if (
            q(
                "#syk013aBasemapSelector"
            )
        ) {
            return;
        }

        const panel =
            findMapPanel();

        if (!panel) {
            return;
        }

        const selector =
            document.createElement(
                "div"
            );

        selector.id =
            "syk013aBasemapSelector";

        selector.className =
            "syk013a-basemap-selector";

        selector.innerHTML = `
            <button
                type="button"
                data-map-mode="harita"
            >
                Harita
            </button>

            <button
                type="button"
                data-map-mode="uydu"
            >
                Uydu
            </button>

            <button
                type="button"
                data-map-mode="arazi"
            >
                Arazi
            </button>

            <button
                type="button"
                data-map-mode="topografya"
            >
                Topografya
            </button>
        `;

        selector
            .querySelectorAll(
                "[data-map-mode]"
            )
            .forEach(
                button => {

                    button.addEventListener(
                        "click",
                        async event => {

                            event.stopPropagation();

                            const mode =
                                button.dataset
                                    .mapMode;

                            try {

                                const state =
                                    await fetchJson(
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

                                setBaseLayer(
                                    L,
                                    state.viewport.mode
                                );

                                markBasemapButton(
                                    state.viewport.mode
                                );
                            }
                            catch(error) {

                                console.error(
                                    "BASEMAP_CHANGE_FAIL",
                                    error
                                );
                            }
                        }
                    );
                }
            );

        panel.appendChild(
            selector
        );

        /*
         * Haritaya dokununca taban harita
         * seçimleri görünür.
         */

        panel.addEventListener(
            "pointerdown",
            event => {

                if (
                    event.target.closest(
                        "#syk013aBasemapSelector"
                    )
                ) {
                    return;
                }

                selector.classList.add(
                    "gorunur"
                );

                clearTimeout(
                    selector._hideTimer
                );

                selector._hideTimer =
                    setTimeout(
                        () => {
                            selector.classList.remove(
                                "gorunur"
                            );
                        },
                        6000
                    );
            }
        );
    }

    function markBasemapButton(
        mode
    ) {

        document
            .querySelectorAll(
                "#syk013aBasemapSelector [data-map-mode]"
            )
            .forEach(
                button => {

                    button.classList.toggle(
                        "aktif",
                        button.dataset.mapMode ===
                        mode
                    );
                }
            );
    }

    async function pullState(
        L
    ) {

        const state =
            await fetchJson(
                STATE_URL
            );

        setBaseLayer(
            L,
            state.viewport.mode
            || "harita"
        );

        syncViewport(
            state
        );

        markBasemapButton(
            state.viewport.mode
            || "harita"
        );
    }

    async function start() {

        removePlaceholder();

        const L =
            await loadLeaflet();

        const state =
            await fetchJson(
                STATE_URL
            );

        createMap(
            L,
            state
        );

        setBaseLayer(
            L,
            state.viewport.mode
            || "harita"
        );

        createBasemapSelector(
            L
        );

        bindModeControls(
            L
        );

        markBasemapButton(
            state.viewport.mode
            || "harita"
        );

        requestGps(
            L
        );

        /*
         * DOM tamamen oturduktan sonra boyutu düzelt.
         */

        setTimeout(
            () => {
                map.invalidateSize(
                    false
                );
            },
            300
        );

        /*
         * Backend viewport/mod değişikliklerini
         * canlı izle.
         */

        setInterval(
            () => {

                pullState(
                    L
                )
                .catch(
                    error =>
                        console.warn(
                            "REAL_MAP_STATE_REFRESH_FAIL",
                            error
                        )
                );
            },
            1500
        );

        document.documentElement
            .dataset.syk013aRuntime =
            "ready";

        console.info(
            "SPRINT_053_013A_REAL_MAP_READY"
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
                            error => {

                                console.error(
                                    "REAL_MAP_START_FAIL",
                                    error
                                );

                                document.documentElement
                                    .dataset.syk013aRuntime =
                                    "error";
                            }
                        );
                    },
                    1000
                );
            }
        );
    }
    else {

        setTimeout(
            () => {
                start().catch(
                    error => {

                        console.error(
                            "REAL_MAP_START_FAIL",
                            error
                        );

                        document.documentElement
                            .dataset.syk013aRuntime =
                            "error";
                    }
                );
            },
            1000
        );
    }

})();
