from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.external_device_routes import (
    external_device_router,
)
from syk_simulasyon.syk_ui_runtime.external_device_runtime import (
    external_device_runtime,
)


def client() -> TestClient:
    external_device_runtime.reset()

    app = FastAPI()
    app.include_router(
        external_device_router
    )

    return TestClient(app)


def test_external_device_api_full_flow() -> None:
    test_client = client()

    register_response = test_client.post(
        "/api/syk-ui/external-devices/garmin/mock",
        json={
            "latitude": 38.7123,
            "longitude": 38.4521,
            "minimum_depth_m": 0.4,
            "maximum_depth_m": 2.0,
            "seed": 42,
        },
    )

    assert register_response.status_code == 201

    registered = register_response.json()

    device_id = (
        registered["profile"]
        ["identity"]["device_id"]
    )

    assert (
        registered["connection_state"]
        == "disconnected"
    )

    list_response = test_client.get(
        "/api/syk-ui/external-devices"
    )

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    connect_response = test_client.post(
        (
            "/api/syk-ui/external-devices/"
            f"{device_id}/connect"
        )
    )

    assert connect_response.status_code == 200
    assert (
        connect_response.json()
        ["connection_state"]
        == "connected"
    )

    frame_response = test_client.post(
        (
            "/api/syk-ui/external-devices/"
            f"{device_id}/frames"
        ),
        json={
            "research_id": "research-001",
            "workspace_id": "workspace-001",
        },
    )

    assert frame_response.status_code == 201

    record = frame_response.json()

    assert 0.4 <= record["frame"]["depth_m"] <= 2.0
    assert (
        record["frame"]["source_mode"]
        == "mock"
    )
    assert (
        record["frame"]["metadata"]
        ["real_device_data"]
        is False
    )
    assert (
        record["evidence_candidate"]
        ["evidence_status"]
        == "candidate-unverified"
    )
    assert (
        record["research_id"]
        == "research-001"
    )
    assert (
        record["workspace_id"]
        == "workspace-001"
    )

    records_response = test_client.get(
        (
            "/api/syk-ui/external-devices/"
            "records/list"
        ),
        params={
            "research_id": "research-001",
        },
    )

    assert records_response.status_code == 200
    assert records_response.json()["count"] == 1

    disconnect_response = test_client.post(
        (
            "/api/syk-ui/external-devices/"
            f"{device_id}/disconnect"
        )
    )

    assert disconnect_response.status_code == 200
    assert (
        disconnect_response.json()
        ["connection_state"]
        == "disconnected"
    )


def test_frame_requires_connection() -> None:
    test_client = client()

    response = test_client.post(
        "/api/syk-ui/external-devices/garmin/mock",
        json={},
    )

    device_id = (
        response.json()["profile"]
        ["identity"]["device_id"]
    )

    frame_response = test_client.post(
        (
            "/api/syk-ui/external-devices/"
            f"{device_id}/frames"
        ),
        json={},
    )

    assert frame_response.status_code == 409


def test_external_device_not_found() -> None:
    test_client = client()

    response = test_client.get(
        "/api/syk-ui/external-devices/missing"
    )

    assert response.status_code == 404


def test_mock_depth_validation() -> None:
    test_client = client()

    response = test_client.post(
        "/api/syk-ui/external-devices/garmin/mock",
        json={
            "minimum_depth_m": 2.0,
            "maximum_depth_m": 1.0,
        },
    )

    assert response.status_code == 422