from syk_simulasyon.syk_ui_runtime.adaptive_environment import (
    AdaptiveEnvironmentEngine,
)


def test_gun_isigi_orani_gece_azalir():
    night = (
        AdaptiveEnvironmentEngine
        .daylight_factor(
            hour=2,
            minute=0,
        )
    )

    noon = (
        AdaptiveEnvironmentEngine
        .daylight_factor(
            hour=12,
            minute=30,
        )
    )

    assert night < noon
    assert night >= 0.12
    assert noon <= 1.0


def test_hava_durumu_parlakligi_etkiler():
    clear = (
        AdaptiveEnvironmentEngine
        .recommended_brightness(
            daylight_factor=0.8,
            weather="clear",
            cloud_percent=5,
        )
    )

    storm = (
        AdaptiveEnvironmentEngine
        .recommended_brightness(
            daylight_factor=0.8,
            weather="storm",
            cloud_percent=95,
        )
    )

    assert clear > storm


def test_runtime_ortami_guncellenir():
    engine = AdaptiveEnvironmentEngine()

    result = engine.update(
        weather="rain",
        temperature_c=14.5,
        wind_speed_kmh=28.0,
        wind_direction_deg=210.0,
        cloud_percent=88.0,
        precipitation_percent=75.0,
    )

    assert result["weather"] == "rain"
    assert result["wind_speed_kmh"] == 28.0
    assert result["source"] == "manual_runtime"