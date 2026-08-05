from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.sensor_fusion_routes import (
    sensor_fusion_router,
)
from syk_simulasyon.syk_ui_runtime.sensor_fusion_runtime import (
    sensor_fusion_runtime,
)
from syk_simulasyon.syk_ui_runtime.sensor_gateway_routes import (
    sensor_gateway_router,
)
from syk_simulasyon.syk_ui_runtime.sensor_gateway_runtime import (
    sensor_gateway_runtime,
)


def client() -> TestClient:
    sensor_fusion_runtime.reset()
    sensor_gateway_runtime.reset()

    app = FastAPI()

    app.include_router(
        sensor_gateway_router
    )

    app.include_router(
        sensor_fusion_router
    )

    return TestClient(app)


def register_source(
    test_client: TestClient,
    source_id: str,
    kind: str,
) -> None:
    response = test_client.post(
        "/api/syk-ui/sensor-gateway/sources",
        json={
            "source_id": source_id,
            "name": source_id,
            "kind": kind,
            "authority": "external-live",
            "health": "healthy",
            "real_device_data": True,
            "simulation_data": False,
        },
    )

    assert response.status_code == 201


def ingest(
    test_client: TestClient,
    source_id: str,
    payload: dict[str, object],
    confidence: float,
) -> None:
    response = test_client.post(
        (
            "/api/syk-ui/sensor-gateway/"
            f"sources/{source_id}/ingest"
        ),
        json={
            "payload": payload,
            "research_id": "research-001",
            "workspace_id": "workspace-001",
            "confidence": confidence,
        },
    )

    assert response.status_code == 201


def test_sensor_fusion_full_flow() -> None:
    test_client = client()

    register_source(
        test_client,
        "sonar-001",
        "sonar",
    )

    register_source(
        test_client,
        "gps-001",
        "gps",
    )

    register_source(
        test_client,
        "water-001",
        "water-temperature",
    )

    ingest(
        test_client,
        "sonar-001",
        {
            "depth_m": 1.42,
            "water_temperature_c": 19.8,
            "gps": {
                "latitude": 38.712301,
                "longitude": 38.452101,
            },
        },
        0.82,
    )

    ingest(
        test_client,
        "gps-001",
        {
            "latitude": 38.712302,
            "longitude": 38.452102,
            "accuracy_m": 0.04,
        },
        0.98,
    )

    ingest(
        test_client,
        "water-001",
        {
            "water_temperature_c": 22.4,
            "latitude": 38.712303,
            "longitude": 38.452103,
        },
        0.90,
    )

    response = test_client.post(
        "/api/syk-ui/sensor-fusion/run",
        json={
            "research_id": "research-001",
            "workspace_id": "workspace-001",
            "time_tolerance_seconds": 10,
            "location_tolerance_m": 20,
            "minimum_source_count": 2,
            "source_weights": {
                "sonar-001": 2.0,
                "gps-001": 3.0,
                "water-001": 1.0,
            },
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["count"] == 1

    group = data["groups"][0]

    assert len(group["source_ids"]) == 3
    assert len(group["envelope_ids"]) == 3

    assert (
        group["combined_confidence"]
        > 0.8
    )

    assert (
        group["real_device_data"]
        is True
    )

    assert (
        group["simulation_data"]
        is False
    )

    assert (
        group["map_layer_packet"]
        ["layer_key"]
        == "sensor-fusion"
    )

    assert (
        len(
            group["evidence_group_id"]
        )
        > 20
    )

    assert (
        group["conflict_count"]
        >= 1
    )

    detail = test_client.get(
        (
            "/api/syk-ui/sensor-fusion/"
            + group["group_id"]
        )
    )

    assert detail.status_code == 200


def test_minimum_source_count_prevents_group() -> None:
    test_client = client()

    register_source(
        test_client,
        "sonar-001",
        "sonar",
    )

    ingest(
        test_client,
        "sonar-001",
        {
            "depth_m": 1.5,
        },
        0.8,
    )

    response = test_client.post(
        "/api/syk-ui/sensor-fusion/run",
        json={
            "research_id": "research-001",
            "workspace_id": "workspace-001",
            "minimum_source_count": 2,
        },
    )

    assert response.status_code == 201
    assert response.json()["count"] == 0


def test_invalid_source_weight_returns_422() -> None:
    test_client = client()

    register_source(
        test_client,
        "sonar-001",
        "sonar",
    )

    register_source(
        test_client,
        "gps-001",
        "gps",
    )

    ingest(
        test_client,
        "sonar-001",
        {
            "depth_m": 1.5,
        },
        0.8,
    )

    ingest(
        test_client,
        "gps-001",
        {
            "latitude": 38.7,
            "longitude": 38.4,
        },
        0.9,
    )

    response = test_client.post(
        "/api/syk-ui/sensor-fusion/run",
        json={
            "research_id": "research-001",
            "workspace_id": "workspace-001",
            "source_weights": {
                "sonar-001": 0,
                "gps-001": 1,
            },
        },
    )

    assert response.status_code == 422


def test_fusion_group_not_found() -> None:
    test_client = client()

    response = test_client.get(
        "/api/syk-ui/sensor-fusion/missing"
    )

    assert response.status_code == 404