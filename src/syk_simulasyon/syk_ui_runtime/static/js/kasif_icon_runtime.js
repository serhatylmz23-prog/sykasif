(() => {
    "use strict";

    const API =
        "/api/syk-ui/kasif-icons";

    const state = {
        icons: new Map(),
        manifest: null,
        loaded: false,
        activeTheme: "gold",
        reducedMotion:
            window.matchMedia(
                "(prefers-reduced-motion: reduce)"
            ).matches,
    };

    async function fetchJson(
        url,
        options = {}
    ) {
        const response = await fetch(
            url,
            {
                headers: {
                    Accept:
                        "application/json",
                    ...(options.headers || {}),
                },
                ...options,
            }
        );

        const payload =
            await response.json();

        if (!response.ok) {
            throw new Error(
                payload.detail
                || "Kaşif ikon işlemi başarısız."
            );
        }

        return payload;
    }

    async function load() {
        const manifest =
            await fetchJson(
                `${API}/manifest`
            );

        state.manifest =
            manifest;

        state.icons.clear();

        for (
            const icon
            of manifest.icons
        ) {
            state.icons.set(
                icon.icon_id,
                icon
            );
        }

        state.loaded = true;

        document.body.dataset
            .sykKasifIcons =
                "ready";

        document.dispatchEvent(
            new CustomEvent(
                "syk:kasif-icons-ready",
                {
                    detail: {
                        iconCount:
                            state.icons.size,
                        manifestSha256:
                            manifest
                                .manifest_sha256,
                    },
                }
            )
        );

        hydrate();

        return manifest;
    }

    function get(iconId) {
        return (
            state.icons.get(
                String(iconId)
                    .trim()
                    .toLowerCase()
            )
            || null
        );
    }

    function all(options = {}) {
        let icons =
            Array.from(
                state.icons.values()
            );

        if (options.group) {
            icons = icons.filter(
                icon =>
                    icon.group
                    === options.group
            );
        }

        if (
            options.enabledOnly
            !== false
        ) {
            icons = icons.filter(
                icon =>
                    icon.enabled
            );
        }

        return icons.sort(
            (left, right) =>
                left.order
                - right.order
        );
    }

    function create(
        iconId,
        options = {}
    ) {
        const icon = get(
            iconId
        );

        if (!icon) {
            throw new Error(
                `Kaşif ikonu bulunamadı: `
                + iconId
            );
        }

        const button =
            options.interactive
            !== false;

        const element =
            document.createElement(
                button
                    ? "button"
                    : "article"
            );

        if (button) {
            element.type =
                "button";
        }

        element.className =
            "syk-kasif-icon";

        element.dataset.iconId =
            icon.icon_id;

        element.dataset.iconGroup =
            icon.group;

        element.dataset.iconTheme =
            options.theme
            || icon.theme
            || state.activeTheme;

        element.dataset.iconAnimation =
            state.reducedMotion
                ? "none"
                : (
                    options.animation
                    || icon.animation
                    || "none"
                );

        element.dataset.assetExists =
            String(
                icon.asset_exists
            );

        element.setAttribute(
            "aria-label",
            options.ariaLabel
            || icon.title
        );

        element.title =
            options.tooltip
            || icon.description;

        const frame =
            document.createElement(
                "span"
            );

        frame.className =
            "syk-kasif-icon__frame";

        const media =
            document.createElement(
                "span"
            );

        media.className =
            "syk-kasif-icon__media";

        const fallback =
            document.createElement(
                "span"
            );

        fallback.className =
            "syk-kasif-icon__fallback";

        fallback.textContent =
            icon.fallback_symbol
            || "✦";

        media.appendChild(
            fallback
        );

        if (icon.asset_exists) {
            const image =
                document.createElement(
                    "img"
                );

            image.className =
                "syk-kasif-icon__image";

            image.src =
                icon.asset_url;

            image.alt = "";

            image.loading =
                options.loading
                || "lazy";

            image.decoding =
                "async";

            image.addEventListener(
                "load",
                () => {
                    fallback.hidden =
                        true;

                    element.dataset
                        .assetLoaded =
                            "true";
                }
            );

            image.addEventListener(
                "error",
                () => {
                    image.remove();

                    fallback.hidden =
                        false;

                    element.dataset
                        .assetLoaded =
                            "false";
                }
            );

            media.appendChild(
                image
            );
        }

        frame.appendChild(
            media
        );

        const title =
            document.createElement(
                "span"
            );

        title.className =
            "syk-kasif-icon__title";

        title.textContent =
            options.title
            || icon.title;

        element.append(
            frame,
            title
        );

        if (
            options.showDescription
        ) {
            const description =
                document.createElement(
                    "span"
                );

            description.className =
                "syk-kasif-icon__description";

            description.textContent =
                icon.description;

            element.appendChild(
                description
            );
        }

        if (button) {
            element.addEventListener(
                "click",
                () => {
                    activate(
                        icon,
                        element,
                        options
                    );
                }
            );
        }

        return element;
    }

    function activate(
        icon,
        element,
        options
    ) {
        document.dispatchEvent(
            new CustomEvent(
                "syk:kasif-icon-activate",
                {
                    detail: {
                        icon,
                        element,
                        moduleId:
                            icon.module_id,
                    },
                }
            )
        );

        if (
            typeof options.onActivate
            === "function"
        ) {
            options.onActivate(
                icon,
                element
            );

            return;
        }

        document.dispatchEvent(
            new CustomEvent(
                "syk:module-open-request",
                {
                    detail: {
                        moduleId:
                            icon.module_id,
                        source:
                            "kasif_icon_registry",
                        iconId:
                            icon.icon_id,
                    },
                }
            )
        );

        if (
            window.SyKJarmin
            && icon.icon_id
            !== "kasif"
        ) {
            document.dispatchEvent(
                new CustomEvent(
                    "syk:kasif-context-changed",
                    {
                        detail: {
                            moduleId:
                                icon.module_id,
                            title:
                                icon.title,
                        },
                    }
                )
            );
        }

        if (
            icon.icon_id
            === "kasif"
            && window.SyKJarmin
        ) {
            window.SyKJarmin.open();
        }
    }

    function renderGrid(
        target,
        options = {}
    ) {
        const host =
            typeof target
            === "string"
                ? document.querySelector(
                    target
                )
                : target;

        if (!host) {
            throw new Error(
                "İkon kütüphanesi hedefi "
                + "bulunamadı."
            );
        }

        host.innerHTML = "";

        host.classList.add(
            "syk-kasif-icon-grid"
        );

        const icons = all({
            group:
                options.group,
            enabledOnly:
                options.enabledOnly,
        });

        for (
            const icon
            of icons
        ) {
            if (
                options.excludeAssistant
                && icon.icon_id
                === "kasif"
            ) {
                continue;
            }

            host.appendChild(
                create(
                    icon.icon_id,
                    {
                        interactive:
                            options
                                .interactive
                            !== false,
                        showDescription:
                            Boolean(
                                options
                                    .showDescription
                            ),
                        theme:
                            options.theme,
                        animation:
                            options.animation,
                        onActivate:
                            options
                                .onActivate,
                    }
                )
            );
        }

        return host;
    }

    function hydrate(
        root = document
    ) {
        const targets =
            root.querySelectorAll(
                "[data-syk-kasif-icon]"
            );

        for (
            const target
            of targets
        ) {
            if (
                target.dataset
                    .kasifIconHydrated
                === "true"
            ) {
                continue;
            }

            const iconId =
                target.dataset
                    .sykKasifIcon;

            const rendered =
                create(
                    iconId,
                    {
                        interactive:
                            target.dataset
                                .interactive
                            !== "false",
                        showDescription:
                            target.dataset
                                .showDescription
                            === "true",
                        theme:
                            target.dataset
                                .theme,
                        animation:
                            target.dataset
                                .animation,
                    }
                );

            target.replaceChildren(
                rendered
            );

            target.dataset
                .kasifIconHydrated =
                    "true";
        }

        const grids =
            root.querySelectorAll(
                "[data-syk-kasif-icon-grid]"
            );

        for (
            const grid
            of grids
        ) {
            if (
                grid.dataset
                    .kasifGridHydrated
                === "true"
            ) {
                continue;
            }

            renderGrid(
                grid,
                {
                    group:
                        grid.dataset
                            .group
                        || null,
                    showDescription:
                        grid.dataset
                            .showDescription
                        === "true",
                    excludeAssistant:
                        grid.dataset
                            .excludeAssistant
                        === "true",
                }
            );

            grid.dataset
                .kasifGridHydrated =
                    "true";
        }
    }

    function setTheme(
        theme
    ) {
        const normalized =
            String(theme)
                .trim()
                .toLowerCase();

        const allowed = new Set([
            "gold",
            "silver",
            "blue",
            "green",
            "red",
            "dark",
        ]);

        if (!allowed.has(
            normalized
        )) {
            throw new Error(
                "Geçersiz Kaşif ikon teması."
            );
        }

        state.activeTheme =
            normalized;

        document.body.dataset
            .sykIconTheme =
                normalized;

        for (
            const element
            of document
                .querySelectorAll(
                    ".syk-kasif-icon"
                )
        ) {
            element.dataset.iconTheme =
                normalized;
        }

        document.dispatchEvent(
            new CustomEvent(
                "syk:kasif-icon-theme-changed",
                {
                    detail: {
                        theme:
                            normalized,
                    },
                }
            )
        );
    }

    function search(
        query
    ) {
        const normalized =
            String(query)
                .trim()
                .toLocaleLowerCase(
                    "tr-TR"
                );

        if (!normalized) {
            return [];
        }

        return all({
            enabledOnly: false,
        }).filter(
            icon => {
                const searchable = [
                    icon.icon_id,
                    icon.title,
                    icon.group,
                    icon.module_id,
                    icon.description,
                    ...(icon.keywords
                        || []),
                ];

                return searchable.some(
                    value =>
                        String(value)
                            .toLocaleLowerCase(
                                "tr-TR"
                            )
                            .includes(
                                normalized
                            )
                );
            }
        );
    }

    function snapshot() {
        return {
            loaded:
                state.loaded,
            iconCount:
                state.icons.size,
            activeTheme:
                state.activeTheme,
            manifestSha256:
                state.manifest
                    ?.manifest_sha256
                || null,
            assistant:
                get("kasif"),
        };
    }

    window.SyKKasifIcons = {
        load,
        get,
        all,
        create,
        renderGrid,
        hydrate,
        setTheme,
        search,
        snapshot,
    };

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            load().catch(
                error => {
                    document.body.dataset
                        .sykKasifIcons =
                            "error";

                    document.dispatchEvent(
                        new CustomEvent(
                            "syk:kasif-icons-error",
                            {
                                detail: {
                                    message:
                                        error.message,
                                },
                            }
                        )
                    );
                }
            );
        },
        {
            once: true,
        }
    );
})();