from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.external_device_routes import (
    external_device_router,
)
from syk_simulasyon.syk_ui_runtime.external_device_runtime import (
    external_device_runtime,
)
from syk_simulasyon.syk_ui_runtime.sonar_session_routes import (
    sonar_session_router,
)
from syk_simulasyon.syk_ui_runtime.sonar_session_runtime import (
    sonar_session_runtime,
)


def client() -> TestClient:
    sonar_session_runtime.reset()
    external_device_runtime.reset()

    app = FastAPI()

    app.include_router(
        external_device_router
    )

    app.include_router(
        sonar_session_router
    )

    return TestClient(app)


def register_and_connect(
    test_client: TestClient,
) -> str:
    response = test_client.post(
        "/api/syk-ui/external-devices/garmin/mock",
        json={
            "minimum_depth_m": 0.4,
            "maximum_depth_m": 2.0,
            "seed": 42,
        },
    )

    assert response.status_code == 201

    device_id = (
        response.json()["profile"]
        ["identity"]["device_id"]
    )

    connected = test_client.post(
        (
            "/api/syk-ui/external-devices/"
            f"{device_id}/connect"
        )
    )

    assert connected.status_code == 200

    return device_id


def test_sonar_session_full_flow() -> None:
    test_client = client()
    device_id = register_and_connect(
        test_client
    )

    create_response = test_client.post(
        "/api/syk-ui/sonar-sessions",
        json={
            "device_id": device_id,
            "name": "Kıyı Şeridi Tarama Oturumu",
            "research_id": "research-001",
            "workspace_id": "workspace-001",
            "maximum_priority_depth_m": 2.0,
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()
    session_id = created["session_id"]

    assert created["state"] == "ready"
    assert created["frame_count"] == 0

    start_response = test_client.post(
        (
            "/api/syk-ui/sonar-sessions/"
            f"{session_id}/start"
        )
    )

    assert start_response.status_code == 200
    assert (
        start_response.json()["state"]
        == "active"
    )

    capture_response = test_client.post(
        (
            "/api/syk-ui/sonar-sessions/"
            f"{session_id}/capture"
        ),
        json={
            "frame_count": 4,
        },
    )

    assert capture_response.status_code == 200

    captured = capture_response.json()

    assert captured["frame_count"] == 4
    assert len(captured["timeline"]) == 4
    assert len(captured["gps_track"]) == 4
    assert (
        len(
            captured[
                "evidence_candidate_ids"
            ]
        )
        == 4
    )

    assert (
        captured["map_layer_state"]
        ["layer_key"]
        == "garmin-sonar-live"
    )

    assert (
        captured["map_layer_state"]
        ["frame_count"]
        == 4
    )

    assert (
        captured["map_layer_state"]
        ["within_priority_depth"]
        is True
    )

    assert (
        captured["summary"]
        ["average_depth_m"]
        is not None
    )

    assert (
        captured["summary"]
        ["fish_target_count"]
        == 2
    )

    stop_response = test_client.post(
        (
            "/api/syk-ui/sonar-sessions/"
            f"{session_id}/stop"
        )
    )

    assert stop_response.status_code == 200
    assert (
        stop_response.json()["state"]
        == "stopped"
    )

    assert (
        stop_response.json()
        ["map_layer_state"]["visible"]
        is False
    )

    list_response = test_client.get(
        "/api/syk-ui/sonar-sessions",
        params={
            "research_id": "research-001",
        },
    )

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1


def test_sonar_session_requires_connection() -> None:
    test_client = client()

    register_response = test_client.post(
        "/api/syk-ui/external-devices/garmin/mock",
        json={},
    )

    device_id = (
        register_response.json()
        ["profile"]["identity"]["device_id"]
    )

    session_response = test_client.post(
        "/api/syk-ui/sonar-sessions",
        json={
            "device_id": device_id,
            "name": "Bağlantısız Oturum",
        },
    )

    session_id = (
        session_response.json()["session_id"]
    )

    start_response = test_client.post(
        (
            "/api/syk-ui/sonar-sessions/"
            f"{session_id}/start"
        )
    )

    assert start_response.status_code == 409


def test_capture_requires_active_session() -> None:
    test_client = client()
    device_id = register_and_connect(
        test_client
    )

    create_response = test_client.post(
        "/api/syk-ui/sonar-sessions",
        json={
            "device_id": device_id,
            "name": "Hazır Oturum",
        },
    )

    session_id = (
        create_response.json()["session_id"]
    )

    capture_response = test_client.post(
        (
            "/api/syk-ui/sonar-sessions/"
            f"{session_id}/capture"
        ),
        json={
            "frame_count": 2,
        },
    )

    assert capture_response.status_code == 409


def test_sonar_session_not_found() -> None:
    test_client = client()

    response = test_client.get(
        "/api/syk-ui/sonar-sessions/missing"
    )

    assert response.status_code == 404