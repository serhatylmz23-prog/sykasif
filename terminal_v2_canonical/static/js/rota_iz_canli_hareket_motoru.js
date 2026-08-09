"use strict";

import {
    ROUTE_TRACE_STATES,
} from "./rota_iz_gorsel_stil_motoru.js";


const MOTION_PROFILES = Object.freeze({
    normal: Object.freeze({
        enabled: false,
        speed: 0,
        pulse: 0,
        dashOffsetSpeed: 0,
    }),

    aktif: Object.freeze({
        enabled: true,
        speed: 0.65,
        pulse: 0.18,
        dashOffsetSpeed: 0.8,
    }),

    secili: Object.freeze({
        enabled: true,
        speed: 0.85,
        pulse: 0.28,
        dashOffsetSpeed: 1.1,
    }),

    uyari: Object.freeze({
        enabled: true,
        speed: 1.05,
        pulse: 0.42,
        dashOffsetSpeed: 1.35,
    }),

    tamamlandi: Object.freeze({
        enabled: false,
        speed: 0,
        pulse: 0,
        dashOffsetSpeed: 0,
    }),
});


function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}


function assertState(state) {
    if (!Object.values(ROUTE_TRACE_STATES).includes(state)) {
        throw new TypeError(`Geçersiz hareket durumu: ${state}`);
    }
}


export function createMotionProfile(
    state = ROUTE_TRACE_STATES.NORMAL,
    options = {},
) {
    assertState(state);

    const base = MOTION_PROFILES[state];

    const speedScale = clamp(
        Number(options.speedScale ?? 1),
        0,
        2,
    );

    return Object.freeze({
        state,
        enabled: Boolean(
            options.enabled ?? base.enabled
        ),
        speed: Number(
            (base.speed * speedScale).toFixed(3)
        ),
        pulse: Number(base.pulse.toFixed(3)),
        dashOffsetSpeed: Number(
            (base.dashOffsetSpeed * speedScale).toFixed(3)
        ),
    });
}


export function createMotionFrame(
    profile,
    elapsedMs = 0,
) {
    if (!profile || typeof profile !== "object") {
        throw new TypeError("Hareket profili gerekli.");
    }

    const elapsed = Math.max(
        0,
        Number(elapsedMs) || 0,
    );

    if (!profile.enabled) {
        return Object.freeze({
            active: false,
            phase: 0,
            pulse: 0,
            dashOffset: 0,
        });
    }

    const seconds = elapsed / 1000;

    const phase = (
        seconds * profile.speed
    ) % 1;

    const pulse = Number(
        (
            Math.sin(phase * Math.PI * 2) *
            profile.pulse
        ).toFixed(4)
    );

    const dashOffset = Number(
        (
            seconds *
            profile.dashOffsetSpeed *
            -10
        ).toFixed(3)
    );

    return Object.freeze({
        active: true,
        phase: Number(phase.toFixed(4)),
        pulse,
        dashOffset,
    });
}


export function applyMotionToVisual(
    visual,
    elapsedMs = 0,
) {
    if (!visual || typeof visual !== "object") {
        throw new TypeError("Görsel sözleşme gerekli.");
    }

    const profile = createMotionProfile(
        visual.state,
        {
            enabled: visual.style?.motion,
        },
    );

    const frame = createMotionFrame(
        profile,
        elapsedMs,
    );

    return Object.freeze({
        ...visual,
        motion: Object.freeze({
            profile,
            frame,
        }),
    });
}


export {
    MOTION_PROFILES,
};
