"use strict";

/**
 * SyKaşif Terminal V2
 * Rota / İz Görsel Stil Motoru
 *
 * Temel ilke:
 * - geometri motorundan bağımsızdır
 * - rota ve iz aynı geometriyi farklı görsel sözleşmelerle gösterebilir
 * - durum, vurgu ve yoğunluk tek merkezden yönetilir
 */

const ROUTE_TRACE_KINDS = Object.freeze({
    ROTA: "rota",
    IZ: "iz",
});

const ROUTE_TRACE_STATES = Object.freeze({
    NORMAL: "normal",
    AKTIF: "aktif",
    SECILI: "secili",
    UYARI: "uyari",
    TAMAMLANDI: "tamamlandi",
});

const BASE_STYLES = Object.freeze({
    rota: Object.freeze({
        width: 3,
        opacity: 0.92,
        dash: Object.freeze([]),
        cap: "round",
        join: "round",
        glow: 0.16,
        motion: false,
    }),

    iz: Object.freeze({
        width: 2,
        opacity: 0.72,
        dash: Object.freeze([5, 7]),
        cap: "round",
        join: "round",
        glow: 0.08,
        motion: false,
    }),
});

const STATE_MODIFIERS = Object.freeze({
    normal: Object.freeze({
        widthScale: 1,
        opacityScale: 1,
        glowScale: 1,
        motion: false,
    }),

    aktif: Object.freeze({
        widthScale: 1.08,
        opacityScale: 1,
        glowScale: 1.5,
        motion: true,
    }),

    secili: Object.freeze({
        widthScale: 1.28,
        opacityScale: 1,
        glowScale: 2,
        motion: true,
    }),

    uyari: Object.freeze({
        widthScale: 1.12,
        opacityScale: 0.95,
        glowScale: 1.8,
        motion: true,
    }),

    tamamlandi: Object.freeze({
        widthScale: 1,
        opacityScale: 0.78,
        glowScale: 0.65,
        motion: false,
    }),
});

function assertKind(kind) {
    if (!Object.values(ROUTE_TRACE_KINDS).includes(kind)) {
        throw new TypeError(`Geçersiz rota/iz türü: ${kind}`);
    }
}

function assertState(state) {
    if (!Object.values(ROUTE_TRACE_STATES).includes(state)) {
        throw new TypeError(`Geçersiz rota/iz durumu: ${state}`);
    }
}

function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}

export function createRouteTraceStyle(
    kind,
    state = ROUTE_TRACE_STATES.NORMAL,
    options = {},
) {
    assertKind(kind);
    assertState(state);

    const base = BASE_STYLES[kind];
    const modifier = STATE_MODIFIERS[state];

    const density = clamp(
        Number.isFinite(Number(options.density))
            ? Number(options.density)
            : 1,
        0.5,
        2,
    );

    const width = Number(
        (
            base.width *
            modifier.widthScale *
            density
        ).toFixed(3),
    );

    const opacity = Number(
        clamp(
            base.opacity * modifier.opacityScale,
            0,
            1,
        ).toFixed(3),
    );

    const glow = Number(
        clamp(
            base.glow * modifier.glowScale,
            0,
            1,
        ).toFixed(3),
    );

    return Object.freeze({
        kind,
        state,
        width,
        opacity,
        dash: base.dash,
        cap: base.cap,
        join: base.join,
        glow,
        motion: Boolean(
            options.motion ?? modifier.motion
        ),
        selected: state === ROUTE_TRACE_STATES.SECILI,
        warning: state === ROUTE_TRACE_STATES.UYARI,
        completed: state === ROUTE_TRACE_STATES.TAMAMLANDI,
    });
}

export function createRouteStyle(
    state = ROUTE_TRACE_STATES.NORMAL,
    options = {},
) {
    return createRouteTraceStyle(
        ROUTE_TRACE_KINDS.ROTA,
        state,
        options,
    );
}

export function createTraceStyle(
    state = ROUTE_TRACE_STATES.NORMAL,
    options = {},
) {
    return createRouteTraceStyle(
        ROUTE_TRACE_KINDS.IZ,
        state,
        options,
    );
}

export function createSegmentVisualState(
    segment,
    style,
) {
    if (!segment || typeof segment !== "object") {
        throw new TypeError("Segment nesnesi gerekli.");
    }

    if (!style || typeof style !== "object") {
        throw new TypeError("Stil nesnesi gerekli.");
    }

    return Object.freeze({
        segmentIndex: Number(segment.index ?? 0),
        start: segment.start ?? null,
        end: segment.end ?? null,
        length: Number(segment.length ?? 0),
        style,
        drawable: Boolean(
            segment.start &&
            segment.end
        ),
    });
}

export {
    ROUTE_TRACE_KINDS,
    ROUTE_TRACE_STATES,
};
