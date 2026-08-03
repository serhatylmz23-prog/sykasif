from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


def test_ortam_api_guncellenir():
    client = TestClient(app)

    response = client.patch(
        "/api/syk-ui/environment/current",
        json={
            "weather": "fog",
            "temperature_c": 9.5,
            "wind_speed_kmh": 7.0,
            "wind_direction_deg": 120.0,
            "cloud_percent": 90.0,
            "precipitation_percent": 15.0,
            "timezone": "Europe/Istanbul",
            "source": "api_test",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["weather"] == "fog"
    assert payload["source"] == "api_test"

    current = client.get(
        "/api/syk-ui/environment/current"
    )

    assert current.status_code == 200

    assert (
        current.json()["weather"]
        == "fog"
    )