(function () {
    "use strict";

    const ROOT_SELECTOR = "[data-syk-ugr-library]";
    const ICON_SELECTOR = "[data-syk-icon-id]";

    const VALID_STATES = new Set([
        "bekliyor",
        "baslatiliyor",
        "calisiyor",
        "tariyor",
        "veri_aktariyor",
        "analiz_ediliyor",
        "dogrulaniyor",
        "senkronize_ediliyor",
        "tamamlandi",
        "uyari",
        "hata",
        "durduruldu",
        "cevrimdisi"
    ]);

    const VALID_VIEWS = new Set([
        "2b",
        "3b",
        "ar"
    ]);

    const STATE_CLASS_PREFIX =
        "syk-ugr-state-";

    const VIEW_CLASS_PREFIX =
        "syk-ugr-view-";

    function removeClassesByPrefix(
        element,
        prefix
    ) {
        Array.from(element.classList)
            .filter(function (className) {
                return className.startsWith(prefix);
            })
            .forEach(function (className) {
                element.classList.remove(className);
            });
    }

    function createRuntimeEvent(
        name,
        detail
    ) {
        return new CustomEvent(
            name,
            {
                bubbles: true,
                detail: detail
            }
        );
    }

    function normalizeState(state) {
        const value = String(state || "")
            .trim()
            .toLowerCase();

        if (!VALID_STATES.has(value)) {
            throw new Error(
                "Geçersiz UGR ikon durumu: "
                + value
            );
        }

        return value;
    }

    function normalizeView(view) {
        const value = String(view || "")
            .trim()
            .toLowerCase();

        if (!VALID_VIEWS.has(value)) {
            throw new Error(
                "Geçersiz UGR görünüm modu: "
                + value
            );
        }

        return value;
    }

    class UgrDynamicIconRuntime {
        constructor(root) {
            this.root = root || document;
            this.icons = new Map();
            this.observer = null;
        }

        initialize() {
            this.scan();
            this.bindClicks();
            this.observe();

            this.root.dispatchEvent(
                createRuntimeEvent(
                    "syk:ugr:runtime-ready",
                    {
                        iconCount: this.icons.size
                    }
                )
            );

            return this;
        }

        scan() {
            const elements =
                this.root.querySelectorAll(
                    ICON_SELECTOR
                );

            elements.forEach(
                (element) => {
                    const id =
                        element.dataset.sykIconId;

                    if (!id) {
                        return;
                    }

                    this.icons.set(
                        id,
                        element
                    );
                }
            );

            return this.icons.size;
        }

        observe() {
            if (
                typeof MutationObserver
                === "undefined"
            ) {
                return;
            }

            this.observer =
                new MutationObserver(
                    (mutations) => {
                        const shouldScan =
                            mutations.some(
                                (mutation) =>
                                    mutation.addedNodes.length
                                    > 0
                            );

                        if (shouldScan) {
                            this.scan();
                        }
                    }
                );

            const target =
                this.root === document
                    ? document.documentElement
                    : this.root;

            this.observer.observe(
                target,
                {
                    childList: true,
                    subtree: true
                }
            );
        }

        bindClicks() {
            this.root.addEventListener(
                "click",
                (event) => {
                    const icon =
                        event.target.closest(
                            ICON_SELECTOR
                        );

                    if (!icon) {
                        return;
                    }

                    icon.dispatchEvent(
                        createRuntimeEvent(
                            "syk:ugr:icon-selected",
                            this.read(icon)
                        )
                    );
                }
            );
        }

        get(iconId) {
            const icon =
                this.icons.get(iconId);

            if (!icon) {
                throw new Error(
                    "UGR ikonu bulunamadı: "
                    + iconId
                );
            }

            return icon;
        }

        read(iconOrId) {
            const icon =
                typeof iconOrId === "string"
                    ? this.get(iconOrId)
                    : iconOrId;

            return {
                iconId:
                    icon.dataset.sykIconId,
                category:
                    icon.dataset.sykCategory,
                label:
                    icon.dataset.sykLabel,
                state:
                    icon.dataset.sykState,
                view:
                    icon.dataset.sykView,
                animation:
                    icon.dataset.sykAnimation,
                colorRole:
                    icon.dataset.sykColorRole,
                active:
                    icon.dataset.sykActive
                    === "true",
                objectId:
                    icon.dataset.sykObjectId
                    || null
            };
        }

        setState(
            iconId,
            state,
            options
        ) {
            const icon = this.get(iconId);
            const nextState =
                normalizeState(state);
            const previousState =
                icon.dataset.sykState;

            removeClassesByPrefix(
                icon,
                STATE_CLASS_PREFIX
            );

            icon.classList.add(
                STATE_CLASS_PREFIX
                + nextState
            );

            icon.dataset.sykState =
                nextState;

            if (
                options
                && options.animation
            ) {
                removeClassesByPrefix(
                    icon,
                    "syk-ugr-animation-"
                );

                icon.classList.add(
                    "syk-ugr-animation-"
                    + options.animation
                );

                icon.dataset.sykAnimation =
                    options.animation;
            }

            if (
                options
                && options.colorRole
            ) {
                removeClassesByPrefix(
                    icon,
                    "syk-ugr-role-"
                );

                icon.classList.add(
                    "syk-ugr-role-"
                    + options.colorRole
                );

                icon.dataset.sykColorRole =
                    options.colorRole;
            }

            if (
                options
                && Number.isFinite(
                    options.durationMs
                )
            ) {
                icon.style.setProperty(
                    "--syk-icon-duration",
                    String(
                        options.durationMs
                    ) + "ms"
                );
            }

            icon.dispatchEvent(
                createRuntimeEvent(
                    "syk:ugr:icon-state-changed",
                    {
                        iconId: iconId,
                        previousState:
                            previousState,
                        nextState:
                            nextState,
                        runtime:
                            this.read(icon)
                    }
                )
            );

            return this.read(icon);
        }

        setView(
            iconId,
            view
        ) {
            const icon = this.get(iconId);
            const nextView =
                normalizeView(view);
            const previousView =
                icon.dataset.sykView;

            removeClassesByPrefix(
                icon,
                VIEW_CLASS_PREFIX
            );

            icon.classList.add(
                VIEW_CLASS_PREFIX
                + nextView
            );

            icon.dataset.sykView =
                nextView;

            icon.dispatchEvent(
                createRuntimeEvent(
                    "syk:ugr:icon-view-changed",
                    {
                        iconId: iconId,
                        previousView:
                            previousView,
                        nextView:
                            nextView,
                        runtime:
                            this.read(icon)
                    }
                )
            );

            return this.read(icon);
        }

        setActive(
            iconId,
            active
        ) {
            const icon = this.get(iconId);
            const normalized =
                Boolean(active);

            icon.dataset.sykActive =
                normalized
                    ? "true"
                    : "false";

            icon.classList.toggle(
                "syk-ugr-icon-inactive",
                !normalized
            );

            icon.disabled =
                !normalized;

            return this.read(icon);
        }

        updateFromPayload(payload) {
            if (
                !payload
                || typeof payload !== "object"
            ) {
                throw new TypeError(
                    "UGR ikon güncelleme verisi nesne olmalıdır."
                );
            }

            const iconId =
                payload.ikon_kimligi
                || payload.iconId;

            if (!iconId) {
                throw new Error(
                    "UGR ikon kimliği eksik."
                );
            }

            if (
                payload.durum
                || payload.state
            ) {
                this.setState(
                    iconId,
                    payload.durum
                        || payload.state,
                    {
                        animation:
                            payload.animasyon
                            || payload.animation,
                        colorRole:
                            payload.renk_rolu
                            || payload.colorRole,
                        durationMs:
                            payload
                                .animasyon_suresi_ms
                            || payload.durationMs
                    }
                );
            }

            if (
                payload.gorunum_modu
                || payload.view
            ) {
                this.setView(
                    iconId,
                    payload.gorunum_modu
                        || payload.view
                );
            }

            if (
                Object.prototype
                    .hasOwnProperty
                    .call(
                        payload,
                        "aktif"
                    )
                || Object.prototype
                    .hasOwnProperty
                    .call(
                        payload,
                        "active"
                    )
            ) {
                this.setActive(
                    iconId,
                    Object.prototype
                        .hasOwnProperty
                        .call(
                            payload,
                            "aktif"
                        )
                        ? payload.aktif
                        : payload.active
                );
            }

            return this.read(
                iconId
            );
        }

        connectEventSource(url) {
            if (
                typeof EventSource
                === "undefined"
            ) {
                throw new Error(
                    "EventSource desteklenmiyor."
                );
            }

            const source =
                new EventSource(url);

            source.addEventListener(
                "ikon_durumu",
                (event) => {
                    const payload =
                        JSON.parse(
                            event.data
                        );

                    this.updateFromPayload(
                        payload
                    );
                }
            );

            source.addEventListener(
                "error",
                () => {
                    this.root.dispatchEvent(
                        createRuntimeEvent(
                            "syk:ugr:stream-error",
                            {
                                url: url
                            }
                        )
                    );
                }
            );

            return source;
        }

        destroy() {
            if (this.observer) {
                this.observer.disconnect();
            }

            this.icons.clear();
        }
    }

    window.SykUgrDynamicIconRuntime =
        UgrDynamicIconRuntime;

    document.addEventListener(
        "DOMContentLoaded",
        function () {
            document
                .querySelectorAll(
                    ROOT_SELECTOR
                )
                .forEach(
                    function (root) {
                        if (
                            root
                                .sykUgrRuntime
                        ) {
                            return;
                        }

                        root.sykUgrRuntime =
                            new UgrDynamicIconRuntime(
                                root
                            ).initialize();
                    }
                );
        }
    );
})();
