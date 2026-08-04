from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


def test_telefon_runtime_api():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/mobile-runtime/devices",
        json={
            "device_id": "PHONE-API-006A",
            "device_type": "phone",
            "title": "Saha Telefonu",
            "platform": "Android",
            "user_agent": "pytest",
            "language": "tr-TR",
            "timezone": "Europe/Istanbul",
            "viewport": {
                "width": 390,
                "height": 844,
                "pixel_ratio": 3.0,
                "orientation": "portrait",
            },
            "capabilities": {
                "touch": True,
                "camera": True,
                "microphone": True,
                "location": True,
                "notification": True,
                "vibration": True,
                "fullscreen": True,
                "wake_lock": True,
                "online": True,
                "input_mode": "touch",
            },
            "trusted": False,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["device"][
            "device_id"
        ]
        == "PHONE-API-006A"
    )

    assert (
        payload["layout"][
            "density"
        ]
        == "compact"
    )


def test_tablet_yerlesim_api():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/mobile-runtime/layout",
        json={
            "device_type": "tablet",
            "viewport": {
                "width": 1280,
                "height": 800,
                "pixel_ratio": 2.0,
                "orientation": "landscape",
            },
            "capabilities": {
                "touch": True,
                "camera": True,
                "microphone": True,
                "location": True,
                "notification": True,
                "vibration": True,
                "fullscreen": True,
                "wake_lock": True,
                "online": True,
                "input_mode": "touch",
            },
        },
    )

    assert response.status_code == 200

    assert (
        response.json()[
            "panel_mode"
        ]
        == "dual_panel"
    )


def test_cihaz_guven_api():
    client = TestClient(app)

    client.post(
        "/api/syk-ui/mobile-runtime/devices",
        json={
            "device_id": "TABLET-TRUST-006A",
            "device_type": "tablet",
            "title": "Güven Test Tableti",
            "platform": "Android",
            "viewport": {
                "width": 800,
                "height": 1280,
                "pixel_ratio": 2.0,
                "orientation": "portrait",
            },
            "capabilities": {
                "touch": True,
                "camera": False,
                "microphone": False,
                "location": False,
                "notification": True,
                "vibration": True,
                "fullscreen": True,
                "wake_lock": False,
                "online": True,
                "input_mode": "touch",
            },
        },
    )

    response = client.patch(
        "/api/syk-ui/mobile-runtime/"
        "devices/TABLET-TRUST-006A/trust",
        json={
            "trusted": True
        },
    )

    assert response.status_code == 200

    assert (
        response.json()[
            "device"
        ]["trusted"]
    )