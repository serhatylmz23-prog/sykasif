from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeSessions:
    def get(self, session_id: str):
        if session_id == "recording":
            return {
                "id": session_id,
                "state": "recording",
            }

        if session_id != "session-001":
            raise KeyError(session_id)

        return {
            "id": session_id,
            "device_id": "serial:COM7",
            "module_id": "gpr",
            "state": "stopped",
            "sample_count": 2,
        }


class FakePackageBuilder:
    def verify(self, session_id: str):
        return {
            "valid": True,
            "session_id": session_id,
        }

    def build(self, *, session: dict):
        return {
            "session_id": session["id"],
            "verification": {
                "valid": True,
            },
        }


class FakeSeal:
    def create(self, *, session: dict):
        return {
            "session_id": session["id"],
            "package_sha256": "a" * 64,
            "report_sha256": "b" * 64,
            "seal_sha256": "c" * 64,
            "verification": {
                "valid": True,
            },
        }

    def verify(self, session_id: str):
        return {
            "valid": True,
            "session_id": session_id,
            "package_sha256": "a" * 64,
            "report_sha256": "b" * 64,
            "seal_sha256": "c" * 64,
        }


def test_cihaz_paket_muhur_api(
    monkeypatch,
):
    monkeypatch.setattr(
        api_routes,
        "scientific_device_sessions",
        FakeSessions(),
    )

    monkeypatch.setattr(
        api_routes,
        "scientific_device_package_builder",
        FakePackageBuilder(),
    )

    monkeypatch.setattr(
        api_routes,
        "scientific_device_package_seal",
        FakeSeal(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    sealed = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/seal"
        )
    )

    assert sealed.status_code == 200
    assert sealed.json()[
        "verification"
    ]["valid"]

    assert len(
        sealed.json()["seal_sha256"]
    ) == 64

    verification = client.get(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/seal/verify"
        )
    )

    assert verification.status_code == 200
    assert verification.json()["valid"]

    active = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "recording/seal"
        )
    )

    assert active.status_code == 409