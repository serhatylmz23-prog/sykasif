from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes
from syk_simulasyon.syk_ui_runtime.scientific_device_evidence import (
    DeviceEvidenceStore,
)


class FakeSessions:
    def __init__(self):
        self.sample_count = 0

    def get(self, session_id: str):
        if session_id != "session-001":
            raise KeyError(session_id)

        return {
            "id": session_id,
            "device_id": "serial:COM7",
            "module_id": "gpr",
            "state": "recording",
            "sample_count": self.sample_count,
        }

    def append_sample(
        self,
        session_id: str,
        *,
        count: int,
    ):
        self.sample_count += count

        return {
            "id": session_id,
            "sample_count": self.sample_count,
        }


def test_cihaz_kanit_api(
    monkeypatch,
    tmp_path,
):
    sessions = FakeSessions()

    monkeypatch.setattr(
        api_routes,
        "scientific_device_sessions",
        sessions,
    )

    monkeypatch.setattr(
        api_routes,
        "scientific_device_evidence",
        DeviceEvidenceStore(
            root=tmp_path
        ),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    first = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/evidence"
        ),
        json={
            "payload": {
                "live_value": 52.4,
                "confidence": 96.1,
                "source": "gpr_test",
            }
        },
    )

    assert first.status_code == 200
    assert first.json()["sequence"] == 1
    assert len(first.json()["sha256"]) == 64

    second = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/evidence"
        ),
        json={
            "payload": {
                "live_value": 53.0,
                "confidence": 96.8,
                "source": "gpr_test",
            }
        },
    )

    assert second.status_code == 200
    assert second.json()["sequence"] == 2
    assert (
        second.json()["previous_hash"]
        == first.json()["sha256"]
    )

    records = client.get(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/evidence"
        )
    )

    assert records.status_code == 200
    assert len(records.json()) == 2

    verification = client.get(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/evidence/verify"
        )
    )

    assert verification.status_code == 200
    assert verification.json()["valid"]
    assert (
        verification.json()["record_count"]
        == 2
    )

    assert sessions.sample_count == 2