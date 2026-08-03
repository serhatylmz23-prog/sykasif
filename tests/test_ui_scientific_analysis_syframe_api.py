from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeBridge:
    def apply(self, session_id: str):
        return {
            "session_id": session_id,
            "analysis_verified": True,
            "analysis_sha256": "a" * 64,
            "decision": {
                "id": "digitally_verified",
                "syframe_state": "verified",
            },
            "trend": {
                "direction": "increasing",
            },
            "anomalies": {
                "count": 0,
            },
            "syframe": {
                "state": {
                    "id": "verified",
                    "title": "Doğrulandı",
                    "color": "#6DFF41",
                },
                "mode": "evidence",
                "visible": True,
                "confidence": 96.4,
            },
            "field_validation_required": True,
        }

    def snapshot(self):
        return {
            "state": {
                "id": "verified",
                "title": "Doğrulandı",
                "color": "#6DFF41",
            },
            "mode": "evidence",
            "visible": True,
            "confidence": 96.4,
        }


def test_analiz_syframe_api(
    monkeypatch,
):
    monkeypatch.setattr(
        api_routes,
        "scientific_analysis_syframe",
        FakeBridge(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    applied = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/syframe"
        )
    )

    assert applied.status_code == 200

    payload = applied.json()

    assert payload[
        "analysis_verified"
    ]

    assert payload["syframe"][
        "state"
    ]["id"] == "verified"

    assert payload["syframe"][
        "mode"
    ] == "evidence"

    assert payload["syframe"][
        "confidence"
    ] == 96.4

    current = client.get(
        "/api/syk-ui/syframe/analysis-state"
    )

    assert current.status_code == 200
    assert current.json()[
        "state"
    ]["id"] == "verified"