from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakePipeline:
    def ingest(
        self,
        *,
        device_id: str,
        payload: dict,
    ):
        return {
            "recorded": True,
            "session": {
                "id": "session-001",
                "device_id": device_id,
                "sample_count": 1,
            },
            "evidence": {
                "sequence": 1,
                "payload": payload,
                "sha256": "a" * 64,
            },
        }


def test_cihaz_kayit_pipeline_api(
    monkeypatch,
):
    monkeypatch.setattr(
        api_routes,
        "scientific_device_recording_pipeline",
        FakePipeline(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    response = client.post(
        (
            "/api/syk-ui/device-hub/"
            "serial:COM7/recording-ingest"
        ),
        json={
            "payload": {
                "transport": "serial",
                "live_value": 48.7,
                "confidence": 95.4,
            }
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["recorded"]
    assert payload["session"]["sample_count"] == 1
    assert payload["evidence"]["sequence"] == 1
    assert len(payload["evidence"]["sha256"]) == 64