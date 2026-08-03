from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeSyFrameBridge:
    def snapshot(self):
        return {
            "state": {
                "id": "rare_anomaly",
                "title": "Nadir Anomali",
                "color": "#B86CFF",
            },
            "mode": "anomaly",
            "visible": True,
            "confidence": 94.6,
        }


def test_analiz_syframe_runtime_snapshotina_eklenir(
    monkeypatch,
):
    monkeypatch.setattr(
        api_routes,
        "scientific_analysis_syframe",
        FakeSyFrameBridge(),
    )

    snapshot = api_routes.get_runtime_state()

    assert snapshot["syframe"]["state"]["id"] == (
        "rare_anomaly"
    )
    assert snapshot["syframe"]["mode"] == "anomaly"
    assert snapshot["syframe"]["visible"]
    assert snapshot["syframe"]["confidence"] == 94.6


def test_analiz_syframe_websocket_ile_yayinlanir(
    monkeypatch,
):
    monkeypatch.setattr(
        api_routes,
        "scientific_analysis_syframe",
        FakeSyFrameBridge(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    with client.websocket_connect(
        "/api/syk-ui/live"
    ) as websocket:
        payload = websocket.receive_json()

    assert payload["connection"] == "live"

    assert payload["syframe"]["state"]["id"] == (
        "rare_anomaly"
    )

    assert payload["syframe"]["state"]["title"] == (
        "Nadir Anomali"
    )

    assert payload["syframe"]["mode"] == "anomaly"
    assert payload["syframe"]["visible"]
    assert payload["syframe"]["confidence"] == 94.6