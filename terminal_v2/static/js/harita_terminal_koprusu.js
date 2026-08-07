"use strict";

const TERMINAL_MAP_BRIDGE_VERSION =
    "SYK_TERMINAL_MAP_BRIDGE_V1";

const MAP_MODULE_CODE =
    "harita";

const MAP_ROUTE =
    "/map";

const MAP_RUNTIME_EVENT =
    "sykasif:aktif-modul-guncellendi";

function mapUrl() {
    return new URL(
        MAP_ROUTE,
        globalThis.location.origin
    ).toString();
}

function openMap() {
    globalThis.location.href =
        MAP_ROUTE;
}

function openMapNewWindow() {
    globalThis.open(
        MAP_ROUTE,
        "_blank",
        "noopener,noreferrer"
    );
}

function isMapModule(value) {

    if (!value) {
        return false;
    }

    const candidates = [
        value.module,
        value.module_id,
        value.modul,
        value.modul_kodu,
        value.aktif_modul,
        value.aktifModul,
        value.code,
        value.kod,
        value.id,
    ];

    return candidates.some(
        (item) =>
            String(
                item ?? ""
            )
                .trim()
                .toLowerCase()
                === MAP_MODULE_CODE
    );
}

function handleRuntimeModuleEvent(
    event
) {
    const detail =
        event?.detail;

    if (
        !isMapModule(detail)
    ) {
        return false;
    }

    globalThis.dispatchEvent(
        new CustomEvent(
            "sykasif:harita-acilacak",
            {
                detail: Object.freeze({
                    module:
                        MAP_MODULE_CODE,

                    route:
                        MAP_ROUTE,

                    url:
                        mapUrl(),
                }),
            }
        )
    );

    return true;
}

function bindTerminalMapBridge() {

    globalThis.addEventListener(
        MAP_RUNTIME_EVENT,
        handleRuntimeModuleEvent
    );

    globalThis.addEventListener(
        "sykasif:harita-ac",
        openMap
    );

    globalThis.addEventListener(
        "sykasif:harita-yeni-pencere",
        openMapNewWindow
    );

    return true;
}

if (
    document.readyState
    === "loading"
) {
    document.addEventListener(
        "DOMContentLoaded",
        bindTerminalMapBridge,
        {
            once: true,
        }
    );
}
else {
    bindTerminalMapBridge();
}

globalThis.SyKasifTerminalMapBridge =
    Object.freeze({
        version:
            TERMINAL_MAP_BRIDGE_VERSION,

        module:
            MAP_MODULE_CODE,

        route:
            MAP_ROUTE,

        runtimeEvent:
            MAP_RUNTIME_EVENT,

        mapUrl,
        openMap,
        openMapNewWindow,
        isMapModule,
        handleRuntimeModuleEvent,
    });

export {
    TERMINAL_MAP_BRIDGE_VERSION,
    MAP_MODULE_CODE,
    MAP_ROUTE,
    MAP_RUNTIME_EVENT,
    mapUrl,
    openMap,
    openMapNewWindow,
    isMapModule,
    handleRuntimeModuleEvent,
    bindTerminalMapBridge,
};