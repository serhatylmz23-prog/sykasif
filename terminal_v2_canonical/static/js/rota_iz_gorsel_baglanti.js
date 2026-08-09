"use strict";

import * as GeometryEngine from "./rota_iz_cizgi_geometrisi.js";

import {
    createRouteTraceStyle,
    ROUTE_TRACE_KINDS,
    ROUTE_TRACE_STATES,
} from "./rota_iz_gorsel_stil_motoru.js";


function normalizeGeometryResult(geometry) {
    if (!geometry || typeof geometry !== "object") {
        return Object.freeze({
            points: Object.freeze([]),
            drawable: false,
        });
    }

    const points = Array.isArray(geometry.points)
        ? geometry.points
        : Array.isArray(geometry.normalized)
            ? geometry.normalized
            : [];

    return Object.freeze({
        points: Object.freeze([...points]),
        drawable: points.length >= 2,
    });
}


export function createRouteTraceVisual(
    geometry,
    kind = ROUTE_TRACE_KINDS.ROTA,
    state = ROUTE_TRACE_STATES.NORMAL,
    options = {},
) {
    const normalizedGeometry = normalizeGeometryResult(geometry);

    const style = createRouteTraceStyle(
        kind,
        state,
        options,
    );

    return Object.freeze({
        kind,
        state,
        geometry: normalizedGeometry,
        style,
        drawable: normalizedGeometry.drawable,
    });
}


export function createRouteVisual(
    geometry,
    state = ROUTE_TRACE_STATES.NORMAL,
    options = {},
) {
    return createRouteTraceVisual(
        geometry,
        ROUTE_TRACE_KINDS.ROTA,
        state,
        options,
    );
}


export function createTraceVisual(
    geometry,
    state = ROUTE_TRACE_STATES.NORMAL,
    options = {},
) {
    return createRouteTraceVisual(
        geometry,
        ROUTE_TRACE_KINDS.IZ,
        state,
        options,
    );
}


export {
    GeometryEngine,
    normalizeGeometryResult,
};
