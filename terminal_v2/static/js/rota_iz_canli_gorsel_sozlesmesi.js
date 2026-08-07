"use strict";

import {
    normalizeRouteTraceGeometry,
} from "./rota_iz_cizgi_geometrisi.js";

import {
    createRouteTraceVisual,
    ROUTE_TRACE_STATES,
} from "./rota_iz_gorsel_stil_motoru.js";

import {
    applyMotionToVisual,
} from "./rota_iz_canli_hareket_motoru.js";


export const ROUTE_TRACE_CONTRACT_VERSION = "1.0.0";


function freezePoints(points) {
    return Object.freeze(
        points.map((point) =>
            Object.freeze({
                x: Number(point.x),
                y: Number(point.y),
            })
        )
    );
}


export function createLiveRouteTraceContract({
    points = [],
    state = ROUTE_TRACE_STATES.NORMAL,
    elapsedMs = 0,
    motion = true,
} = {}) {
    const geometry = normalizeRouteTraceGeometry(points);

    const visual = createRouteTraceVisual(
        geometry,
        state,
        {
            motion,
        },
    );

    const liveVisual = applyMotionToVisual(
        visual,
        elapsedMs,
    );

    return Object.freeze({
        contract: "SYK_ROUTE_TRACE_LIVE_VISUAL",
        version: ROUTE_TRACE_CONTRACT_VERSION,

        geometry: Object.freeze({
            ...geometry,
            points: freezePoints(geometry.points ?? []),
        }),

        state,

        style: Object.freeze({
            ...liveVisual.style,
        }),

        motion: Object.freeze({
            profile: liveVisual.motion.profile,
            frame: liveVisual.motion.frame,
        }),

        drawable:
            Array.isArray(geometry.points) &&
            geometry.points.length >= 2,
    });
}


export function updateLiveRouteTraceFrame(
    contract,
    elapsedMs,
) {
    if (!contract || typeof contract !== "object") {
        throw new TypeError("Canlı rota sözleşmesi gerekli.");
    }

    return createLiveRouteTraceContract({
        points: contract.geometry?.points ?? [],
        state: contract.state,
        elapsedMs,
        motion: contract.motion?.profile?.enabled ?? false,
    });
}


export function isLiveRouteTraceContract(value) {
    return Boolean(
        value &&
        value.contract === "SYK_ROUTE_TRACE_LIVE_VISUAL" &&
        value.version === ROUTE_TRACE_CONTRACT_VERSION &&
        value.geometry &&
        value.style &&
        value.motion
    );
}
