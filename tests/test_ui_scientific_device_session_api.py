from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeSessions:
    def inventory(self):
        return []

    def start(
        self,
        *,
        device_id: str,
        module_id=None,
        metadata=None,
    ):
        return {
            "id": "session-001",
            "device_id": device_id,
            "module_id": module_id or "gpr",
            "state": "recording",
            "started_at": "2026-08-03T00:00:00+00:00",
            "stopped_at": None,
            "sample_count": 0,
            "metadata": metadata or {},
        }

    def get(self, session_id: str):
        return {
            "id": session_id,
            "state": "recording",
        }

    def append_sample(
        self,
        session_id: str,
        *,
        count: int,
    ):
        return {
            "id": session_id,
            "state": "recording",
            "sample_count": count,
        }

    def stop(self, session_id: str):
        return {
            "id": session_id,
            "state": "stopped",
        }


def test_cihaz_kayit_oturumu_api(monkeypatch):
    monkeypatch.setattr(
        api_routes,
        "scientific_device_sessions",
        FakeSessions(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    started = client.post(
        "/api/syk-ui/device-sessions/start",
        json={
            "device_id": "serial:COM7",
            "module_id": "gpr",
            "metadata": {
                "origin": "test",
            },
        },
    )

    assert started.status_code == 200
    assert started.json()["state"] == "recording"

    session_id = started.json()["id"]

    samples = client.post(
        (
            "/api/syk-ui/device-sessions/"
            f"{session_id}/samples"
        ),
        json={
            "count": 50,
        },
    )

    assert samples.status_code == 200
    assert samples.json()["sample_count"] == 50

    stopped = client.post(
        (
            "/api/syk-ui/device-sessions/"
            f"{session_id}/stop"
        )
    )

    assert stopped.status_code == 200
    assert stopped.json()["state"] == "stopped"