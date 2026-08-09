"use strict";

/**
 * SyKaşif Terminal V2
 * Rota / İz çizgi geometrisi çekirdeği.
 *
 * Amaç:
 * - rota ve iz noktalarını normalize etmek
 * - ardışık tekrarları temizlemek
 * - segment geometrisi üretmek
 * - toplam çizgi uzunluğunu hesaplamak
 * - sınır kutusu ve merkez üretmek
 */

export function normalizePoint(point) {
    if (!point || typeof point !== "object") {
        throw new TypeError("Nokta nesne olmalıdır.");
    }

    const x = Number(point.x);
    const y = Number(point.y);

    if (!Number.isFinite(x) || !Number.isFinite(y)) {
        throw new TypeError("Nokta koordinatları sonlu sayı olmalıdır.");
    }

    return Object.freeze({ x, y });
}

export function normalizePoints(points) {
    if (!Array.isArray(points)) {
        throw new TypeError("Noktalar dizi olmalıdır.");
    }

    const result = [];

    for (const rawPoint of points) {
        const point = normalizePoint(rawPoint);
        const previous = result[result.length - 1];

        if (
            previous &&
            previous.x === point.x &&
            previous.y === point.y
        ) {
            continue;
        }

        result.push(point);
    }

    return Object.freeze(result);
}

export function segmentLength(a, b) {
    const p1 = normalizePoint(a);
    const p2 = normalizePoint(b);

    return Math.hypot(
        p2.x - p1.x,
        p2.y - p1.y
    );
}

export function buildSegments(points) {
    const normalized = normalizePoints(points);

    if (normalized.length < 2) {
        return Object.freeze([]);
    }

    const segments = [];

    for (let index = 1; index < normalized.length; index += 1) {
        const start = normalized[index - 1];
        const end = normalized[index];
        const length = segmentLength(start, end);

        segments.push(
            Object.freeze({
                index: index - 1,
                start,
                end,
                length,
            })
        );
    }

    return Object.freeze(segments);
}

export function totalLength(points) {
    return buildSegments(points).reduce(
        (total, segment) => total + segment.length,
        0
    );
}

export function bounds(points) {
    const normalized = normalizePoints(points);

    if (normalized.length === 0) {
        return null;
    }

    let minX = normalized[0].x;
    let minY = normalized[0].y;
    let maxX = normalized[0].x;
    let maxY = normalized[0].y;

    for (const point of normalized) {
        minX = Math.min(minX, point.x);
        minY = Math.min(minY, point.y);
        maxX = Math.max(maxX, point.x);
        maxY = Math.max(maxY, point.y);
    }

    return Object.freeze({
        minX,
        minY,
        maxX,
        maxY,
        width: maxX - minX,
        height: maxY - minY,
        center: Object.freeze({
            x: (minX + maxX) / 2,
            y: (minY + maxY) / 2,
        }),
    });
}

export function createLineGeometry(points, kind = "rota") {
    if (kind !== "rota" && kind !== "iz") {
        throw new TypeError("Geometri türü 'rota' veya 'iz' olmalıdır.");
    }

    const normalized = normalizePoints(points);

    return Object.freeze({
        kind,
        points: normalized,
        segments: buildSegments(normalized),
        totalLength: totalLength(normalized),
        bounds: bounds(normalized),
        empty: normalized.length === 0,
        drawable: normalized.length >= 2,
    });
}
