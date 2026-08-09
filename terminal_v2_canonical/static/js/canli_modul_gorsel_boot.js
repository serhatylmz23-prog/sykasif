"use strict";

import {
    bindCanliModulGorselDurumMotoru,
} from "./canli_modul_gorsel_durum_motoru.js";

const SYK_MODULE_VISUAL_BOOT_KEY =
    "__SYK_MODULE_VISUAL_BOOT_V1__";

function motoruBagla() {
    if (globalThis[SYK_MODULE_VISUAL_BOOT_KEY]) {
        return globalThis[SYK_MODULE_VISUAL_BOOT_KEY];
    }

    const binding =
        bindCanliModulGorselDurumMotoru(window);

    const state = Object.freeze({
        mounted: true,
        binding,
    });

    globalThis[SYK_MODULE_VISUAL_BOOT_KEY] =
        state;

    return state;
}

function bootCanliModulGorselDurumMotoru() {
    if (globalThis[SYK_MODULE_VISUAL_BOOT_KEY]) {
        return globalThis[SYK_MODULE_VISUAL_BOOT_KEY];
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            motoruBagla,
            {
                once: true,
            }
        );

        return Object.freeze({
            mounted: false,
            waiting: true,
        });
    }

    return motoruBagla();
}

bootCanliModulGorselDurumMotoru();

export {
    SYK_MODULE_VISUAL_BOOT_KEY,
    motoruBagla,
    bootCanliModulGorselDurumMotoru,
};
