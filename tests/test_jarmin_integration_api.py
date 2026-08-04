from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


def test_jarmin_entegrasyon_api():
    client = TestClient(app)

    state = client.get(
        "/api/syk-ui/jarmin/integration"
    )

    assert state.status_code == 200

    assert (
        state.json()["status"]
        == "ready"
    )


def test_jarmin_ayar_api():
    client = TestClient(app)

    response = client.patch(
        "/api/syk-ui/jarmin/"
        "integration/settings",
        json={
            "voice_enabled": False,
            "theme_mode": "silver",
        },
    )

    assert response.status_code == 200

    settings = response.json()[
        "settings"
    ]["settings"]

    assert not settings[
        "voice_enabled"
    ]

    assert (
        settings["theme_mode"]
        == "silver"
    )


def test_dtse_olayi_apiye_aktarilir():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/jarmin/"
        "integration/events",
        json={
            "event_type": (
                "dtse_evidence"
            ),
            "source": "dtse",
            "message": (
                "Kanıt kaydı oluşturuldu."
            ),
            "payload": {
                "record_sha256": (
                    "b" * 64
                )
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["event_type"]
        == "dtse_evidence"
    )

    assert payload["notification"]