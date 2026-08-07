"use strict";

import {
    bindTerminalRouteTraceLifecycle,
} from "./rota_iz_terminal_yasam_dongusu.js";


const SYK_ROUTE_TRACE_BOOT_KEY =
    "__SYK_ROUTE_TRACE_BOOT_V1__";


function boot() {
    if (globalThis[SYK_ROUTE_TRACE_BOOT_KEY]) {
        return globalThis[SYK_ROUTE_TRACE_BOOT_KEY];
    }

    const state =
        bindTerminalRouteTraceLifecycle({
            state: "aktif",
            motion: true,
        });

    globalThis[SYK_ROUTE_TRACE_BOOT_KEY] =
        Object.freeze({
            mounted: true,
            state,
        });

    return globalThis[SYK_ROUTE_TRACE_BOOT_KEY];
}


boot();

export {
    boot,
    SYK_ROUTE_TRACE_BOOT_KEY,
};
