"use strict";

import {
    createLiveRouteTraceContract,
    updateLiveRouteTraceFrame,
    isLiveRouteTraceContract,
} from "./rota_iz_canli_gorsel_sozlesmesi.js";


const SVG_NS = "http://www.w3.org/2000/svg";


function assertSvgRoot(svgRoot) {
    if (
        !svgRoot ||
        typeof svgRoot.appendChild !== "function"
    ) {
        throw new TypeError("Geçerli SVG kökü gerekli.");
    }
}


function createSvgElement(name) {
    return document.createElementNS(
        SVG_NS,
        name,
    );
}


function pointsToPath(points) {
    if (!Array.isArray(points) || points.length < 2) {
        return "";
    }

    return points
        .map((point, index) => {
            const command = index === 0 ? "M" : "L";
            return `${command} ${point.x} ${point.y}`;
        })
        .join(" ");
}


function applyContractToPath(path, contract) {
    const style = contract.style ?? {};
    const frame = contract.motion?.frame ?? {};

    path.setAttribute(
        "d",
        pointsToPath(contract.geometry?.points ?? []),
    );

    path.setAttribute(
        "fill",
        "none",
    );

    if (style.stroke) {
        path.setAttribute("stroke", style.stroke);
    }

    if (style.strokeWidth !== undefined) {
        path.setAttribute(
            "stroke-width",
            String(style.strokeWidth),
        );
    }

    if (style.dashArray) {
        path.setAttribute(
            "stroke-dasharray",
            String(style.dashArray),
        );
    }

    path.setAttribute(
        "stroke-dashoffset",
        String(frame.dashOffset ?? 0),
    );

    path.dataset.sykRouteState = contract.state;
    path.dataset.sykRouteDrawable =
        String(contract.drawable);
}


export function createLiveRouteTraceRenderer({
    svgRoot,
    points = [],
    state,
    motion = true,
} = {}) {
    assertSvgRoot(svgRoot);

    let contract = createLiveRouteTraceContract({
        points,
        state,
        elapsedMs: 0,
        motion,
    });

    const path = createSvgElement("path");

    path.setAttribute(
        "data-syk-route-trace",
        "true",
    );

    applyContractToPath(
        path,
        contract,
    );

    svgRoot.appendChild(path);

    function render(elapsedMs = 0) {
        contract = updateLiveRouteTraceFrame(
            contract,
            elapsedMs,
        );

        applyContractToPath(
            path,
            contract,
        );

        return contract;
    }

    function setState(nextState) {
        contract = createLiveRouteTraceContract({
            points: contract.geometry?.points ?? [],
            state: nextState,
            elapsedMs: 0,
            motion,
        });

        applyContractToPath(
            path,
            contract,
        );

        return contract;
    }

    function destroy() {
        if (path.parentNode) {
            path.parentNode.removeChild(path);
        }
    }

    return Object.freeze({
        path,
        render,
        setState,
        destroy,

        getContract() {
            return contract;
        },

        isValid() {
            return isLiveRouteTraceContract(contract);
        },
    });
}


export {
    pointsToPath,
};
