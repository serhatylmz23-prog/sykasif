"use strict";

import {
    createLiveRouteTraceRenderer,
} from "./rota_iz_canli_renderer.js";


export const ROUTE_TRACE_LAYER_ID =
    "syk-route-trace-layer";


function assertContainer(container) {
    if (
        !container ||
        typeof container.appendChild !== "function"
    ) {
        throw new TypeError(
            "Terminal V2 çizim kapsayıcısı gerekli."
        );
    }
}


function createSvgLayer(container) {
    const existing =
        container.querySelector?.(
            `#${ROUTE_TRACE_LAYER_ID}`
        );

    if (existing) {
        return existing;
    }

    const svg = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "svg",
    );

    svg.setAttribute(
        "id",
        ROUTE_TRACE_LAYER_ID,
    );

    svg.setAttribute(
        "data-syk-live-route-layer",
        "true",
    );

    svg.setAttribute(
        "width",
        "100%",
    );

    svg.setAttribute(
        "height",
        "100%",
    );

    svg.setAttribute(
        "viewBox",
        "0 0 1000 1000",
    );

    svg.style.position = "absolute";
    svg.style.inset = "0";
    svg.style.pointerEvents = "none";
    svg.style.overflow = "visible";

    container.appendChild(svg);

    return svg;
}


export function mountRouteTraceLayer({
    container,
    points = [],
    state,
    motion = true,
} = {}) {
    assertContainer(container);

    const svgRoot =
        createSvgLayer(container);

    const renderer =
        createLiveRouteTraceRenderer({
            svgRoot,
            points,
            state,
            motion,
        });

    let animationFrameId = null;
    let startedAt = null;
    let running = false;

    function frame(timestamp) {
        if (!running) {
            return;
        }

        if (startedAt === null) {
            startedAt = timestamp;
        }

        renderer.render(
            timestamp - startedAt
        );

        animationFrameId =
            requestAnimationFrame(frame);
    }

    function start() {
        if (running) {
            return;
        }

        running = true;
        startedAt = null;

        animationFrameId =
            requestAnimationFrame(frame);
    }

    function stop() {
        running = false;

        if (animationFrameId !== null) {
            cancelAnimationFrame(
                animationFrameId
            );

            animationFrameId = null;
        }
    }

    function setState(nextState) {
        return renderer.setState(
            nextState
        );
    }

    function destroy() {
        stop();
        renderer.destroy();

        if (
            svgRoot.childElementCount === 0 &&
            svgRoot.parentNode
        ) {
            svgRoot.parentNode.removeChild(
                svgRoot
            );
        }
    }

    if (motion) {
        start();
    }

    return Object.freeze({
        svgRoot,
        renderer,
        start,
        stop,
        setState,
        destroy,

        isRunning() {
            return running;
        },
    });
}


export function findRouteTraceContainer(
    root = document,
) {
    return (
        root.querySelector(
            "[data-syk-route-container]"
        ) ||
        root.querySelector(
            "#syk-ui-screen"
        ) ||
        root.querySelector(
            "main"
        )
    );
}
