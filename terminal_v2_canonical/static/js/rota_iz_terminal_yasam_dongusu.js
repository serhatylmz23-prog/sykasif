"use strict";

import {
    findRouteTraceContainer,
    mountRouteTraceLayer,
} from "./rota_iz_terminal_ekran_koprusu.js";


let activeRuntime = null;


function defaultRoutePoints() {
    return Object.freeze([
        Object.freeze({ x: 120, y: 760 }),
        Object.freeze({ x: 280, y: 640 }),
        Object.freeze({ x: 470, y: 560 }),
        Object.freeze({ x: 690, y: 390 }),
        Object.freeze({ x: 860, y: 240 }),
    ]);
}


export function mountTerminalRouteTrace({
    root = document,
    points = defaultRoutePoints(),
    state = "aktif",
    motion = true,
} = {}) {
    if (activeRuntime) {
        return activeRuntime;
    }

    const container =
        findRouteTraceContainer(root);

    if (!container) {
        throw new Error(
            "SYK_ROUTE_TRACE_CONTAINER_NOT_FOUND"
        );
    }

    if (
        typeof getComputedStyle === "function" &&
        getComputedStyle(container).position === "static"
    ) {
        container.style.position = "relative";
    }

    activeRuntime =
        mountRouteTraceLayer({
            container,
            points,
            state,
            motion,
        });

    return activeRuntime;
}


export function unmountTerminalRouteTrace() {
    if (!activeRuntime) {
        return false;
    }

    activeRuntime.destroy();
    activeRuntime = null;

    return true;
}


export function getTerminalRouteTraceRuntime() {
    return activeRuntime;
}


export function bootTerminalRouteTrace(
    options = {},
) {
    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            () => mountTerminalRouteTrace(options),
            { once: true },
        );

        return "waiting";
    }

    mountTerminalRouteTrace(options);

    return "mounted";
}


export function bindTerminalRouteTraceLifecycle(
    options = {},
) {
    const bootState =
        bootTerminalRouteTrace(options);

    window.addEventListener(
        "pagehide",
        unmountTerminalRouteTrace,
        { once: true },
    );

    return bootState;
}
