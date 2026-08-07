"use strict";

import {
    HARITA_NESNELERI,
} from "./harita_katman_mimarisi.js";

const ENGINE_VERSION =
    "SYK_REAL_BASEMAP_LEAFLET_V1";

const TURKIYE = Object.freeze({
    lat: 39.0,
    lon: 35.0,
    zoom: 6,
});

const BASEMAPS =
    Object.freeze({

        street: Object.freeze({
            name:
                "OpenStreetMap",

            url:
                "https://tile.openstreetmap.org/{z}/{x}/{y}.png",

            options: {
                maxZoom: 19,

                attribution:
                    "© OpenStreetMap contributors",
            },
        }),

        satellite: Object.freeze({
            name:
                "Uydu",

            url:
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",

            options: {
                maxZoom: 19,

                attribution:
                    "Tiles © Esri",
            },
        }),

        terrain: Object.freeze({
            name:
                "Arazi",

            url:
                "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",

            options: {
                maxZoom: 17,

                attribution:
                    "© OpenTopoMap contributors",
            },
        }),
    });

const layerGroups =
    new Map();

const activeLayers =
    new Set([
        "arastirma_noktasi",
        "fotograf",
        "video",
        "ses",
        "olcum",
        "rota",
        "iz",
        "kamp",
        "kazi",
        "numune",
        "risk",
        "kanit",
    ]);

let map = null;
let currentBasemap = null;
let currentBasemapCode = null;

function byId(id) {
    return document.getElementById(id);
}

function ensureLeaflet() {

    if (
        typeof globalThis.L
        === "undefined"
    ) {
        throw new Error(
            "LEAFLET_NOT_LOADED"
        );
    }

    return globalThis.L;
}

function setBasemapState(text) {

    const node =
        byId(
            "syk-basemap-state"
        );

    if (node) {
        node.textContent =
            text;
    }
}

function setViewButton(code) {

    document
        .querySelectorAll(
            "[data-syk-basemap]"
        )
        .forEach(
            (button) => {

                button.classList.toggle(
                    "active",
                    button.dataset.sykBasemap
                        === code
                );
            }
        );
}

function setBasemap(code) {

    const L =
        ensureLeaflet();

    const config =
        BASEMAPS[code];

    if (!config) {
        throw new Error(
            `UNKNOWN_BASEMAP: ${code}`
        );
    }

    if (currentBasemap) {
        map.removeLayer(
            currentBasemap
        );
    }

    setBasemapState(
        `${config.name} yükleniyor...`
    );

    currentBasemap =
        L.tileLayer(
            config.url,
            {
                ...config.options,

                crossOrigin:
                    true,

                updateWhenIdle:
                    false,

                keepBuffer:
                    3,
            }
        );

    currentBasemap.on(
        "load",
        () => {

            setBasemapState(
                `${config.name} aktif`
            );
        }
    );

    currentBasemap.on(
        "tileerror",
        () => {

            setBasemapState(
                `${config.name} tile erişim hatası`
            );
        }
    );

    currentBasemap.addTo(
        map
    );

    currentBasemapCode =
        code;

    setViewButton(
        code
    );
}

function markerIcon() {

    const L =
        ensureLeaflet();

    return L.divIcon({
        className:
            "",

        html:
            `
            <div class="syk-map-marker">
                <span class="syk-map-marker-inner"></span>
            </div>
            `,

        iconSize:
            [18,18],

        iconAnchor:
            [9,9],
    });
}

function objectRow(
    key,
    value
) {

    return `
        <div class="syk-object-row">
            <div class="syk-object-key">
                ${String(key)}
            </div>

            <div>
                ${String(value ?? "")}
            </div>
        </div>
    `;
}

function showObject(
    object
) {

    const panel =
        byId(
            "syk-object-panel"
        );

    const title =
        byId(
            "syk-object-title"
        );

    const content =
        byId(
            "syk-object-content"
        );

    if (
        !panel
        || !title
        || !content
    ) {
        return;
    }

    title.textContent =
        object.ad
        ?? object.id
        ?? "Nesne";

    const rows = [
        objectRow(
            "ID",
            object.id
        ),

        objectRow(
            "Katman",
            object.katman
        ),

        objectRow(
            "Geometri",
            object.geometri?.type
        ),
    ];

    if (
        object.geometri?.type
        === "Point"
    ) {
        const [
            lon,
            lat,
        ] =
            object.geometri.coordinates;

        rows.push(
            objectRow(
                "Enlem",
                Number(lat).toFixed(6)
            )
        );

        rows.push(
            objectRow(
                "Boylam",
                Number(lon).toFixed(6)
            )
        );
    }

    if (
        object.veri
        && typeof object.veri
        === "object"
    ) {

        for (
            const [
                key,
                value,
            ]
            of Object.entries(
                object.veri
            )
        ) {

            rows.push(
                objectRow(
                    key,
                    value
                )
            );
        }
    }

    content.innerHTML =
        rows.join("");

    panel.dataset.open =
        "true";
}

function closeObject() {

    const panel =
        byId(
            "syk-object-panel"
        );

    if (panel) {
        panel.dataset.open =
            "false";
    }
}

function createPointLayer(
    object
) {

    const L =
        ensureLeaflet();

    const [
        lon,
        lat,
    ] =
        object.geometri.coordinates;

    const marker =
        L.marker(
            [
                lat,
                lon,
            ],
            {
                icon:
                    markerIcon(),
            }
        );

    marker.on(
        "click",
        () => {
            showObject(
                object
            );
        }
    );

    return marker;
}

function createLineLayer(
    object
) {

    const L =
        ensureLeaflet();

    const latlngs =
        object.geometri.coordinates
            .map(
                (
                    [
                        lon,
                        lat,
                    ]
                ) => [
                    lat,
                    lon,
                ]
            );

    const polyline =
        L.polyline(
            latlngs,
            {
                weight:
                    3,

                opacity:
                    0.85,

                dashArray:
                    object.katman === "iz"
                        ? "8 7"
                        : null,
            }
        );

    polyline.on(
        "click",
        () => {
            showObject(
                object
            );
        }
    );

    return polyline;
}

function createPolygonLayer(
    object
) {

    const L =
        ensureLeaflet();

    const rings =
        object.geometri.coordinates
            .map(
                (ring) =>
                    ring.map(
                        (
                            [
                                lon,
                                lat,
                            ]
                        ) => [
                            lat,
                            lon,
                        ]
                    )
            );

    const polygon =
        L.polygon(
            rings,
            {
                weight:
                    2,

                fillOpacity:
                    0.18,
            }
        );

    polygon.on(
        "click",
        () => {
            showObject(
                object
            );
        }
    );

    return polygon;
}

function createObjectLayer(
    object
) {

    switch (
        object.geometri?.type
    ) {

        case "Point":
            return createPointLayer(
                object
            );

        case "LineString":
            return createLineLayer(
                object
            );

        case "Polygon":
            return createPolygonLayer(
                object
            );

        default:
            return null;
    }
}

function buildObjectLayers() {

    const L =
        ensureLeaflet();

    for (
        const object
        of HARITA_NESNELERI
    ) {

        if (
            !layerGroups.has(
                object.katman
            )
        ) {
            layerGroups.set(
                object.katman,
                L.layerGroup()
            );
        }

        const objectLayer =
            createObjectLayer(
                object
            );

        if (objectLayer) {

            objectLayer.addTo(
                layerGroups.get(
                    object.katman
                )
            );
        }
    }

    for (
        const [
            code,
            group,
        ]
        of layerGroups
    ) {

        if (
            activeLayers.has(
                code
            )
        ) {
            group.addTo(
                map
            );
        }
    }
}

function setObjectLayer(
    code,
    active
) {

    const group =
        layerGroups.get(
            code
        );

    if (!group) {
        return;
    }

    if (active) {

        activeLayers.add(
            code
        );

        if (
            !map.hasLayer(
                group
            )
        ) {
            group.addTo(
                map
            );
        }
    }
    else {

        activeLayers.delete(
            code
        );

        if (
            map.hasLayer(
                group
            )
        ) {
            map.removeLayer(
                group
            );
        }
    }
}

function updateCoordinate(
    lat,
    lon
) {

    const node =
        byId(
            "syk-coordinate-box"
        );

    if (!node) {
        return;
    }

    node.innerHTML =
        `
        Enlem: ${lat.toFixed(6)}<br>
        Boylam: ${lon.toFixed(6)}
        `;
}

function updateMapState() {

    const center =
        map.getCenter();

    const zoom =
        map.getZoom();

    const centerNode =
        byId(
            "syk-center-state"
        );

    const zoomNode =
        byId(
            "syk-zoom-state"
        );

    if (centerNode) {

        centerNode.textContent =
            `Merkez ${center.lat.toFixed(5)}, ${center.lng.toFixed(5)}`;
    }

    if (zoomNode) {

        zoomNode.textContent =
            `Zoom ${zoom}`;
    }
}

function bindControls() {

    document
        .querySelectorAll(
            "[data-syk-basemap]"
        )
        .forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    () => {

                        const code =
                            button.dataset.sykBasemap;

                        if (code) {
                            setBasemap(
                                code
                            );
                        }
                    }
                );
            }
        );

    document
        .querySelectorAll(
            "[data-syk-layer]"
        )
        .forEach(
            (input) => {

                input.addEventListener(
                    "change",
                    () => {

                        const code =
                            input.dataset.sykLayer;

                        if (!code) {
                            return;
                        }

                        setObjectLayer(
                            code,
                            Boolean(
                                input.checked
                            )
                        );
                    }
                );
            }
        );

    byId(
        "syk-go-turkiye"
    )?.addEventListener(
        "click",
        () => {

            map.setView(
                [
                    TURKIYE.lat,
                    TURKIYE.lon,
                ],

                TURKIYE.zoom
            );
        }
    );

    byId(
        "syk-object-close"
    )?.addEventListener(
        "click",
        closeObject
    );
}

function boot() {

    const L =
        ensureLeaflet();

    map =
        L.map(
            "syk-real-map",
            {
                zoomControl:
                    true,

                preferCanvas:
                    true,

                worldCopyJump:
                    true,

                minZoom:
                    3,

                maxZoom:
                    19,
            }
        );

    map.setView(
        [
            TURKIYE.lat,
            TURKIYE.lon,
        ],
        TURKIYE.zoom
    );

    setBasemap(
        "street"
    );

    buildObjectLayers();

    bindControls();

    map.on(
        "mousemove",
        (event) => {

            updateCoordinate(
                event.latlng.lat,
                event.latlng.lng
            );
        }
    );

    map.on(
        "moveend",
        updateMapState
    );

    map.on(
        "zoomend",
        updateMapState
    );

    updateMapState();

    globalThis.SyKasifRealMap =
        Object.freeze({
            engine:
                ENGINE_VERSION,

            map,

            basemaps:
                BASEMAPS,

            setBasemap,

            setObjectLayer,

            layerGroups,

            activeLayers,
        });

    return true;
}

if (
    document.readyState
    === "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        boot,
        {
            once:
                true,
        }
    );
}
else {
    boot();
}

export {
    ENGINE_VERSION,
    BASEMAPS,
    TURKIYE,
    boot,
    setBasemap,
    setObjectLayer,
};