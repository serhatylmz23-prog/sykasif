from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


def test_mobil_kontrol_api():
    client = TestClient(app)

    created = client.post(
        "/api/syk-ui/mobile-control/"
        "devices",
        json={
            "device_id": (
                "PHONE-CONTROL-API-006D"
            ),
            "device_type": "phone",
        },
    )

    assert created.status_code == 200

    updated = client.patch(
        "/api/syk-ui/mobile-control/"
        "devices/"
        "PHONE-CONTROL-API-006D",
        json={
            "camera_state": "active",
            "microphone_state": "active",
            "location_state": "active",
            "notification_permission": (
                "granted"
            ),
            "connection_state": "online",
            "pairing_state": "paired",
            "offline_queue_count": 4,
            "fullscreen": True,
            "wake_lock": True,
        },
    )

    assert updated.status_code == 200

    state = updated.json()[
        "state"
    ]

    assert (
        state["camera_state"]
        == "active"
    )

    assert (
        state["pairing_state"]
        == "paired"
    )


def test_mobil_kontrol_liste_api():
    client = TestClient(app)

    response = client.get(
        "/api/syk-ui/mobile-control/"
        "devices"
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list,
    )


def test_bilinmeyen_cihaz_404():
    client = TestClient(app)

    response = client.get(
        "/api/syk-ui/mobile-control/"
        "devices/UNKNOWN-006D"
    )

    assert response.status_code == 404