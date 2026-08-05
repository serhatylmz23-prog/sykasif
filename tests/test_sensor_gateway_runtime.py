from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.sensor_gateway_routes import (
    sensor_gateway_router,
)
from syk_simulasyon.syk_ui_runtime.sensor_gateway_runtime import (
    sensor_gateway_runtime,
)


def client() -> TestClient:
    sensor_gateway_runtime.reset()

    app = FastAPI()
    app.include_router(
        sensor_gateway_router
    )

    return TestClient(app)


def test_sensor_gateway_full_flow() -> None:
    test_client = client()

    source_response = test_client.post(
        "/api/syk-ui/sensor-gateway/sources",
        json={
            "source_id": "garmin-sonar-live-001",
            "name": "Garmin Sonar",
            "kind": "sonar",
            "authority": "external-live",
            "health": "healthy",
            "real_device_data": True,
            "simulation_data": False,
            "metadata": {
                "profile": "shallow-coast-0-2m",
            },
        },
    )

    assert source_response.status_code == 201

    ingest_response = test_client.post(
        (
            "/api/syk-ui/sensor-gateway/"
            "sources/garmin-sonar-live-001/ingest"
        ),
        json={
            "payload": {
                "depth_m": 1.44,
                "water_temperature_c": 19.7,
                "fish_target_count": 1,
            },
            "research_id": "research-001",
            "workspace_id": "workspace-001",
            "confidence": 0.81,
        },
    )

    assert ingest_response.status_code == 201

    envelope = ingest_response.json()

    assert envelope["sequence"] == 1
    assert envelope["real_device_data"] is True
    assert envelope["simulation_data"] is False
    assert envelope["payload"]["depth_m"] == 1.44

    list_response = test_client.get(
        "/api/syk-ui/sensor-gateway/envelopes",
        params={
            "research_id": "research-001",
        },
    )

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    snapshot_response = test_client.get(
        "/api/syk-ui/sensor-gateway"
    )

    assert snapshot_response.status_code == 200

    snapshot = snapshot_response.json()

    assert snapshot["source_count"] == 1
    assert snapshot["envelope_count"] == 1
    assert len(snapshot["manifest_sha256"]) == 64


def test_real_and_simulation_flags_cannot_mix() -> None:
    test_client = client()

    response = test_client.post(
        "/api/syk-ui/sensor-gateway/sources",
        json={
            "source_id": "invalid-source",
            "name": "Invalid",
            "kind": "generic",
            "authority": "external-live",
            "health": "healthy",
            "real_device_data": True,
            "simulation_data": True,
        },
    )

    assert response.status_code == 422


def test_missing_source_returns_404() -> None:
    test_client = client()

    response = test_client.post(
        (
            "/api/syk-ui/sensor-gateway/"
            "sources/missing/ingest"
        ),
        json={
            "payload": {
                "value": 1,
            },
        },
    )

    assert response.status_code == 404


def test_simulation_source_isolated() -> None:
    test_client = client()

    response = test_client.post(
        "/api/syk-ui/sensor-gateway/sources",
        json={
            "source_id": "simulation-sonar-001",
            "name": "Simulation Sonar",
            "kind": "sonar",
            "authority": "simulation",
            "health": "healthy",
            "real_device_data": False,
            "simulation_data": True,
        },
    )

    assert response.status_code == 201

    source = response.json()

    assert source["real_device_data"] is False
    assert source["simulation_data"] is True