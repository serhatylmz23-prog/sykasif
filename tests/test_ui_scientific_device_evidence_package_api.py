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
    def build(self, *, session: dict):
        return {
            "session_id": session["id"],
            "package_path": (
                "artifacts/session-001.zip"
            ),
            "package_size": 2048,
            "package_sha256": "a" * 64,
            "verification": {
                "valid": True,
                "record_count": 2,
            },
        }

    def verify(self, session_id: str):
        return {
            "valid": True,
            "session_id": session_id,
            "record_count": 2,
            "package_sha256": "a" * 64,
        }


def test_cihaz_kanit_paketi_api(
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

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    build = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/package"
        )
    )

    assert build.status_code == 200
    assert build.json()[
        "verification"
    ]["valid"]

    assert len(
        build.json()["package_sha256"]
    ) == 64

    verify = client.get(
        (
            "/api/syk-ui/device-sessions/"
            "session-001/package/verify"
        )
    )

    assert verify.status_code == 200
    assert verify.json()["valid"]
    assert verify.json()[
        "record_count"
    ] == 2

    active = client.post(
        (
            "/api/syk-ui/device-sessions/"
            "recording/package"
        )
    )

    assert active.status_code == 409