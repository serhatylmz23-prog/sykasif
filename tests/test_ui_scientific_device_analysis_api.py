from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeAnalysis:
    def analyze(self, session_id: str):
        return {
            "session_id": session_id,
            "record_count": 10,
            "digital_confidence": 96.4,
            "decision": {
                "id": "digitally_verified",
                "title": "Dijital Olarak Doğrulandı",
                "syframe_state": "verified",
            },
            "analysis_sha256": "a" * 64,
        }

    def get(self, session_id: str):
        return self.analyze(session_id)

    def verify(self, session_id: str):
        return {
            "valid": True,
            "session_id": session_id,
            "analysis_sha256": "a" * 64,
        }


def test_cihaz_oturum_analiz_api(monkeypatch):
    monkeypatch.setattr(
        api_routes,
        "scientific_device_analysis",
        FakeAnalysis(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    analysis = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/analysis"
        )
    )

    assert analysis.status_code == 200
    assert (
        analysis.json()["decision"]["syframe_state"]
        == "verified"
    )

    saved = client.get(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/analysis"
        )
    )

    assert saved.status_code == 200

    verification = client.get(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/analysis/verify"
        )
    )

    assert verification.status_code == 200
    assert verification.json()["valid"]