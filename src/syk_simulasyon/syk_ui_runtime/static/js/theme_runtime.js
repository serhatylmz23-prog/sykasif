(() => {
    "use strict";

    const API = "/api/syk-ui/themes";

    function deviceKind() {
        const width = window.innerWidth;

        if (width <= 700) {
            return "mobile";
        }

        if (width <= 1200) {
            return "tablet";
        }

        return "desktop";
    }

    function apply(theme) {
        const root =
            document.documentElement;

        const body =
            document.body;

        body.dataset.sykTheme =
            theme.id;

        root.style.setProperty(
            "--syk-theme-accent",
            theme.colors.accent
        );

        root.style.setProperty(
            "--syk-theme-secondary",
            theme.colors.secondary
        );

        root.style.setProperty(
            "--syk-theme-surface",
            theme.colors.surface
        );

        root.style.setProperty(
            "--syk-theme-text",
            theme.colors.text
        );

        root.style.setProperty(
            "--syk-theme-logo",
            `url("${theme.assets.logo}")`
        );

        root.style.setProperty(
            "--syk-theme-background",
            `url("${theme.assets.background}")`
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:theme-changed",
                {
                    detail: theme,
                }
            )
        );
    }

    async function fetchJson(
        url,
        options = {}
    ) {
        const response = await fetch(
            url,
            {
                headers: {
                    "Content-Type":
                        "application/json",
                    Accept:
                        "application/json",
                },
                ...options,
            }
        );

        if (!response.ok) {
            throw new Error(
                `${response.status}`
            );
        }

        return response.json();
    }

    async function automatic() {
        const weather =
            document.body.dataset
                .sykWeather
            || "clear";

        const payload = await fetchJson(
            `${API}/automatic`,
            {
                method: "POST",
                body: JSON.stringify({
                    hour:
                        new Date().getHours(),
                    weather,
                    device: deviceKind(),
                }),
            }
        );

        apply(payload.active);

        return payload;
    }

    async function select(
        themeId
    ) {
        const payload = await fetchJson(
            `${API}/current`,
            {
                method: "PUT",
                body: JSON.stringify({
                    theme_id: themeId,
                }),
            }
        );

        apply(payload.active);

        return payload;
    }

    async function start() {
        try {
            await automatic();
        }
        catch {
            document.body.dataset
                .sykTheme = "dark";
        }
    }

    window.SyKThemeRuntime = {
        select,
        automatic,
        current: () =>
            document.body.dataset
                .sykTheme,
    };

    document.addEventListener(
        "DOMContentLoaded",
        start,
        {
            once: true,
        }
    );

    document.addEventListener(
        "syk:environment-updated",
        automatic
    );
})();