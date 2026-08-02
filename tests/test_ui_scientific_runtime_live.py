from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_bilimsel_runtime_patch_ve_websocket():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    updated = client.patch(
        "/api/syk-ui/scientific-modules/thermal",
        json={
            "live_value": 28.75,
            "confidence": 96.4,
            "status": "verified",
            "source": "test_adapter",
        },
    )

    assert updated.status_code == 200

    payload = updated.json()

    assert payload["state"]["live_value"] == 28.75
    assert payload["state"]["confidence"] == 96.4
    assert payload["state"]["status"] == "verified"
    assert payload["state"]["source"] == "test_adapter"
    assert payload["state"]["sequence"] == 2

    with client.websocket_connect(
        "/api/syk-ui/scientific-modules/thermal/live"
    ) as socket:
        live = socket.receive_json()

    assert live["definition"]["id"] == "thermal"
    assert live["state"]["live_value"] == 28.75
    assert live["state"]["confidence"] == 96.4
    assert live["state"]["status"] == "verified"
    assert live["state"]["source"] == "test_adapter"


def test_bilimsel_runtime_patch_bilinmeyen_modul():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    response = client.patch(
        "/api/syk-ui/scientific-modules/unknown",
        json={
            "live_value": 1,
        },
    )

    assert response.status_code == 404