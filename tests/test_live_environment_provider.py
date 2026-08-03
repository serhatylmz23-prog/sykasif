from datetime import UTC, datetime

from syk_simulasyon.syk_ui_runtime.live_environment_provider import (
    LiveEnvironmentProvider,
    LiveEnvironmentRequest,
)


def _payload():
    return {
        "latitude": 39.9,
        "longitude": 32.8,
        "timezone": "Europe/Istanbul",
        "current": {
            "time": (
                "2026-08-03T15:00"
            ),
            "temperature_2m": 29.4,
            "weather_code": 61,
            "cloud_cover": 74,
            "precipitation": 1.2,
            "wind_speed_10m": 18.5,
            "wind_direction_10m": 215,
            "is_day": 1,
        },
        "daily": {
            "sunrise": [
                "2026-08-03T05:47"
            ],
            "sunset": [
                "2026-08-03T19:58"
            ],
            "daylight_duration": [
                51060
            ],
        },
    }


def test_canli_meteoroloji_normalize_edilir():
    provider = LiveEnvironmentProvider(
        fetcher=lambda _: _payload()
    )

    result = provider.fetch(
        LiveEnvironmentRequest(
            latitude=39.9,
            longitude=32.8,
        )
    )

    assert result["weather"] == "rain"
    assert result["temperature_c"] == 29.4
    assert result["sunrise"]
    assert result["sunset"]
    assert result["source"] == "open_meteo"
    assert result["live_weather_connected"]


def test_ay_evresi_uretilir():
    result = (
        LiveEnvironmentProvider
        .moon_state(
            datetime(
                2026,
                8,
                3,
                tzinfo=UTC,
            )
        )
    )

    assert result["phase"]
    assert (
        0.0
        <= result["illumination"]
        <= 1.0
    )


def test_gecersiz_konum_reddedilir():
    try:
        LiveEnvironmentRequest(
            latitude=120.0,
            longitude=20.0,
        ).validate()
    except ValueError as error:
        assert "Enlem" in str(error)
    else:
        raise AssertionError(
            "Geçersiz enlem kabul edildi."
        )