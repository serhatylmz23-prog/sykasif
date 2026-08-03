from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)
from syk_simulasyon.syk_ui_runtime import (
    adaptive_environment_routes,
)
from syk_simulasyon.syk_ui_runtime.live_environment_provider import (
    LiveEnvironmentProvider,
)


def test_canli_ortam_api(
    monkeypatch,
):
    payload = {
        "latitude": 41.0,
        "longitude": 29.0,
        "timezone": "Europe/Istanbul",
        "current": {
            "time": (
                "2026-08-03T15:00"
            ),
            "temperature_2m": 27.0,
            "weather_code": 0,
            "cloud_cover": 5,
            "precipitation": 0,
            "wind_speed_10m": 9,
            "wind_direction_10m": 40,
            "is_day": 1,
        },
        "daily": {
            "sunrise": [
                "2026-08-03T06:02"
            ],
            "sunset": [
                "2026-08-03T20:15"
            ],
            "daylight_duration": [
                51180
            ],
        },
    }

    monkeypatch.setattr(
        adaptive_environment_routes,
        "live_environment_provider",
        LiveEnvironmentProvider(
            fetcher=lambda _: payload
        ),
    )

    client = TestClient(app)

    response = client.get(
        "/api/syk-ui/environment/live",
        params={
            "latitude": 41.0,
            "longitude": 29.0,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["weather"] == "clear"
    assert result["sunrise"]
    assert result["moon_phase"]