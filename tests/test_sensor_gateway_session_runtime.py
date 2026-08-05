from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.sensor_gateway_routes import (
    sensor_gateway_router,
)
from syk_simulasyon.syk_ui_runtime.sensor_gateway_runtime import (
    sensor_gateway_runtime,
)
from syk_simulasyon.syk_ui_runtime.sensor_gateway_session_routes import (
    sensor_gateway_session_router,
)
from syk_simulasyon.syk_ui_runtime.sensor_gateway_session_runtime import (
    sensor_gateway_session_runtime,
)


def client() -> TestClient:
    sensor_gateway_session_runtime.reset()
    sensor_gateway_runtime.reset()

    app = FastAPI()

    app.include_router(
        sensor_gateway_router
    )

    app.include_router(
        sensor_gateway_session_router
    )

    return TestClient(app)


def register_source(
    test_client: TestClient,
    *,
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
    *,
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


def test_multi_sensor_session_full_flow() -> None:
    test_client = client()

    register_source(
        test_client,
        source_id="garmin-sonar-001",
        kind="sonar",
    )

    register_source(
        test_client,
        source_id="gps-rtk-001",
        kind="gps",
    )

    session_response = test_client.post(
        "/api/syk-ui/sensor-sessions",
        json={
            "name": "Birleşik Kıyı Araştırması",
            "source_ids": [
                "garmin-sonar-001",
                "gps-rtk-001",
            ],
            "research_id": "research-001",
            "workspace_id": "workspace-001",
        },
    )

    assert session_response.status_code == 201

    session_id = (
        session_response.json()["session_id"]
    )

    start_response = test_client.post(
        (
            "/api/syk-ui/sensor-sessions/"
            f"{session_id}/start"
        )
    )

    assert start_response.status_code == 200
    assert start_response.json()["state"] == "active"

    ingest(
        test_client,
        source_id="gps-rtk-001",
        payload={
            "latitude": 38.712301,
            "longitude": 38.452101,
            "accuracy_m": 0.04,
        },
        confidence=0.98,
    )

    ingest(
        test_client,
        source_id="garmin-sonar-001",
        payload={
            "depth_m": 1.42,
            "water_temperature_c": 19.8,
            "fish_target_count": 1,
            "gps": {
                "latitude": 38.712302,
                "longitude": 38.452102,
            },
        },
        confidence=0.82,
    )

    sync_response = test_client.post(
        (
            "/api/syk-ui/sensor-sessions/"
            f"{session_id}/sync"
        )
    )

    assert sync_response.status_code == 200

    synced = sync_response.json()

    assert synced["envelope_count"] == 2
    assert len(synced["timeline"]) == 2
    assert len(synced["gps_track"]) == 2

    assert (
        len(
            synced[
                "evidence_candidate_ids"
            ]
        )
        == 2
    )

    assert (
        synced["summary"]
        ["source_counts"]
        ["garmin-sonar-001"]
        == 1
    )

    assert (
        synced["summary"]
        ["source_counts"]
        ["gps-rtk-001"]
        == 1
    )

    assert (
        synced["summary"]
        ["average_confidence"]
        == 0.9
    )

    assert (
        synced["source_health"]
        ["garmin-sonar-001"]
        == "healthy"
    )

    stop_response = test_client.post(
        (
            "/api/syk-ui/sensor-sessions/"
            f"{session_id}/stop"
        )
    )

    assert stop_response.status_code == 200
    assert stop_response.json()["state"] == "stopped"


def test_session_requires_existing_sources() -> None:
    test_client = client()

    response = test_client.post(
        "/api/syk-ui/sensor-sessions",
        json={
            "name": "Eksik Kaynak",
            "source_ids": [
                "missing-source",
            ],
        },
    )

    assert response.status_code == 404


def test_sync_requires_active_session() -> None:
    test_client = client()

    register_source(
        test_client,
        source_id="sonar-001",
        kind="sonar",
    )

    response = test_client.post(
        "/api/syk-ui/sensor-sessions",
        json={
            "name": "Hazır Oturum",
            "source_ids": [
                "sonar-001",
            ],
        },
    )

    session_id = response.json()["session_id"]

    sync_response = test_client.post(
        (
            "/api/syk-ui/sensor-sessions/"
            f"{session_id}/sync"
        )
    )

    assert sync_response.status_code == 409


def test_session_not_found() -> None:
    test_client = client()

    response = test_client.get(
        "/api/syk-ui/sensor-sessions/missing"
    )

    assert response.status_code == 404