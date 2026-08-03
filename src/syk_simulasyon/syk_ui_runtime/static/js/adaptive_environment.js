(() => {
    "use strict";

    const state = {
        sensor: null,
        sensorLux: null,
        environment: null,
        timer: null,
    };

    function clamp(
        value,
        minimum,
        maximum
    ) {
        return Math.min(
            maximum,
            Math.max(
                minimum,
                value
            )
        );
    }

    function luxBrightness(lux) {
        if (!Number.isFinite(lux)) {
            return null;
        }

        if (lux <= 2) {
            return 0.42;
        }

        if (lux <= 20) {
            return 0.54;
        }

        if (lux <= 150) {
            return 0.70;
        }

        if (lux <= 1000) {
            return 0.86;
        }

        return 1.0;
    }

    function applyBrightness(
        environment
    ) {
        const sensorValue =
            luxBrightness(
                state.sensorLux
            );

        const recommended =
            Number(
                environment
                    ?.recommended_brightness
                ?? 0.72
            );

        const brightness = clamp(
            sensorValue === null
                ? recommended
                : (
                    sensorValue * 0.62
                    + recommended * 0.38
                ),
            0.34,
            1.0
        );

        document.documentElement.style
            .setProperty(
                "--syk-screen-brightness",
                brightness.toFixed(3)
            );

        document.documentElement.style
            .setProperty(
                "--syk-ambient-lux",
                String(
                    state.sensorLux
                    ?? -1
                )
            );

        document.body.dataset
            .sykBrightnessMode =
                state.sensorLux === null
                    ? "time-weather"
                    : "ambient-sensor";
    }

    function applyEnvironment(
        environment
    ) {
        state.environment =
            environment;

        const root =
            document.documentElement;

        const body =
            document.body;

        body.dataset.sykWeather =
            environment.weather;

        body.dataset.sykSeason =
            environment.season;

        body.dataset.sykDayPhase =
            environment
                .daylight_factor
                < 0.22
                ? "night"
                : (
                    environment
                        .daylight_factor
                        < 0.58
                        ? "transition"
                        : "day"
                );

        body.dataset
            .sykWeatherSource =
                environment.source;

        body.dataset.sykMoonPhase =
            environment.moon_phase
            || "unknown";

        root.style.setProperty(
            "--syk-moon-illumination",
            Number(
                environment
                    .moon_illumination
                || 0
            ).toFixed(3)
        );

        if (environment.sunrise) {
            root.style.setProperty(
                "--syk-sunrise",
                `"${environment.sunrise}"`
            );
        }

        if (environment.sunset) {
            root.style.setProperty(
                "--syk-sunset",
                `"${environment.sunset}"`
            );
        }

        root.style.setProperty(
            "--syk-daylight-factor",
            environment.daylight_factor
        );

        root.style.setProperty(
            "--syk-cloud-factor",
            (
                environment.cloud_percent
                / 100
            ).toFixed(3)
        );

        root.style.setProperty(
            "--syk-rain-factor",
            (
                environment
                    .precipitation_percent
                / 100
            ).toFixed(3)
        );

        root.style.setProperty(
            "--syk-wind-speed",
            `${Math.max(
                1,
                environment.wind_speed_kmh
            )}s`
        );

        root.style.setProperty(
            "--syk-wind-angle",
            `${environment
                .wind_direction_deg}deg`
        );

        applyBrightness(
            environment
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:environment-updated",
                {
                    detail: environment,
                }
            )
        );
    }

    async function refreshWithLocation(
        latitude,
        longitude
    ) {
        const query =
            new URLSearchParams({
                latitude:
                    String(latitude),
                longitude:
                    String(longitude),
            });

        const response = await fetch(
            `/api/syk-ui/environment/live?${query}`,
            {
                headers: {
                    Accept:
                        "application/json",
                },
            }
        );

        if (!response.ok) {
            throw new Error(
                `${response.status}`
            );
        }

        const payload =
            await response.json();

        applyEnvironment(payload);

        document.body.dataset
            .sykLocationMode =
                "device";

        return payload;
    }

    function requestLocation() {
        return new Promise(
            (
                resolve,
                reject
            ) => {
                if (
                    !navigator.geolocation
                ) {
                    reject(
                        new Error(
                            "geolocation_unavailable"
                        )
                    );
                    return;
                }

                navigator.geolocation
                    .getCurrentPosition(
                        position => {
                            resolve({
                                latitude:
                                    position
                                        .coords
                                        .latitude,
                                longitude:
                                    position
                                        .coords
                                        .longitude,
                                accuracy:
                                    position
                                        .coords
                                        .accuracy,
                            });
                        },
                        reject,
                        {
                            enableHighAccuracy:
                                false,
                            timeout: 8000,
                            maximumAge:
                                15 * 60 * 1000,
                        }
                    );
            }
        );
    }

    async function refresh() {
        try {
            const location =
                await requestLocation();

            document.documentElement
                .style
                .setProperty(
                    "--syk-location-accuracy",
                    String(
                        location.accuracy
                    )
                );

            await refreshWithLocation(
                location.latitude,
                location.longitude
            );

            return;
        }
        catch {
            document.body.dataset
                .sykLocationMode =
                    "fallback";
        }

        try {
            const response = await fetch(
                "/api/syk-ui/environment/current",
                {
                    headers: {
                        Accept:
                            "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `${response.status}`
                );
            }

            applyEnvironment(
                await response.json()
            );
        }
        catch {
            applyEnvironment({
                weather: "clear",
                season: "summer",
                daylight_factor: 0.72,
                recommended_brightness: 0.76,
                cloud_percent: 10,
                precipitation_percent: 0,
                wind_speed_kmh: 5,
                wind_direction_deg: 0,
                source: "browser_fallback",
            });
        }
    }

    function startAmbientSensor() {
        if (
            !("AmbientLightSensor" in window)
        ) {
            return;
        }

        try {
            const sensor =
                new AmbientLightSensor({
                    frequency: 1,
                });

            sensor.addEventListener(
                "reading",
                () => {
                    state.sensorLux =
                        Number(
                            sensor.illuminance
                        );

                    if (
                        state.environment
                    ) {
                        applyBrightness(
                            state.environment
                        );
                    }
                }
            );

            sensor.addEventListener(
                "error",
                () => {
                    state.sensorLux =
                        null;
                }
            );

            sensor.start();

            state.sensor = sensor;
        }
        catch {
            state.sensorLux = null;
        }
    }

    function ensureAtmosphere() {
        if (
            document.querySelector(
                "#syk-dynamic-atmosphere"
            )
        ) {
            return;
        }

        const atmosphere =
            document.createElement(
                "div"
            );

        atmosphere.id =
            "syk-dynamic-atmosphere";

        atmosphere.setAttribute(
            "aria-hidden",
            "true"
        );

        atmosphere.innerHTML = `
            <div class="syk-weather-clouds"></div>
            <div class="syk-weather-rain"></div>
            <div class="syk-weather-snow"></div>
            <div class="syk-weather-fog"></div>
            <div class="syk-weather-storm"></div>
        `;

        document.body.prepend(
            atmosphere
        );
    }

    function start() {
        ensureAtmosphere();
        startAmbientSensor();
        refresh();

        state.timer = window.setInterval(
            refresh,
            5 * 60 * 1000
        );
    }

    window.SyKAdaptiveEnvironment = {
        refresh,
        snapshot: () => ({
            sensorLux:
                state.sensorLux,
            environment:
                state.environment,
        }),
    };

    document.addEventListener(
        "DOMContentLoaded",
        start,
        {
            once: true,
        }
    );
})();