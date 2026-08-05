from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_core.external_devices.nmea_model import (
    calculate_checksum,
)
from syk_simulasyon.syk_ui_runtime.real_device_connection_routes import (
    real_device_connection_router,
)
from syk_simulasyon.syk_ui_runtime.real_device_connection_runtime import (
    real_device_connection_runtime,
)


def sentence(payload: str) -> str:
    return (
        f"${payload}*"
        f"{calculate_checksum(payload)}"
    )


def client() -> TestClient:
    real_device_connection_runtime.reset()

    app = FastAPI()
    app.include_router(
        real_device_connection_router
    )

    return TestClient(app)


def create_connection(
    test_client: TestClient,
) -> str:
    response = test_client.post(
        "/api/syk-ui/real-device-connections",
        json={
            "manufacturer": "Garmin",
            "model": "NMEA Runtime Device",
            "serial_number": "GARMIN-RUNTIME-001",
            "device_id": "garmin-runtime-001",
            "transport": "tcp",
            "host": "127.0.0.1",
            "port": 10110,
        },
    )

    assert response.status_code == 201

    return response.json()["connection_id"]


def test_real_connection_full_flow() -> None:
    test_client = client()
    connection_id = create_connection(
        test_client
    )

    connected = test_client.post(
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/connect"
        )
    )

    assert connected.status_code == 200

    heartbeat = test_client.post(
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/heartbeat"
        )
    )

    assert heartbeat.status_code == 200
    assert heartbeat.json()["heartbeat_count"] == 1

    depth = test_client.post(
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/nmea"
        ),
        json={
            "sentence": sentence(
                "SDDPT,1.44,0.00"
            ),
        },
    )

    assert depth.status_code == 200

    temperature = test_client.post(
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/nmea"
        ),
        json={
            "sentence": sentence(
                "YXMTW,19.7,C"
            ),
        },
    )

    assert temperature.status_code == 200

    snapshot = temperature.json()[
        "connection_snapshot"
    ]

    assert snapshot["depth_m"] == 1.44
    assert snapshot["water_temperature_c"] == 19.7
    assert snapshot["real_device_data"] is True

    manifest = test_client.get(
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/manifest"
        )
    )

    assert manifest.status_code == 200

    data = manifest.json()

    assert data["real_device_data"] is True
    assert data["simulation_data"] is False
    assert len(data["digest_sha256"]) == 64

    disconnected = test_client.post(
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/disconnect"
        )
    )

    assert disconnected.status_code == 200


def test_heartbeat_requires_connection() -> None:
    test_client = client()
    connection_id = create_connection(
        test_client
    )

    response = test_client.post(
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/heartbeat"
        )
    )

    assert response.status_code == 409


def test_mock_transport_is_rejected() -> None:
    test_client = client()

    response = test_client.post(
        "/api/syk-ui/real-device-connections",
        json={
            "manufacturer": "Garmin",
            "model": "Invalid",
            "serial_number": "INVALID-001",
            "device_id": "invalid-001",
            "transport": "mock",
        },
    )

    assert response.status_code == 422


def test_connection_not_found() -> None:
    test_client = client()

    response = test_client.get(
        "/api/syk-ui/real-device-connections/missing"
    )

    assert response.status_code == 404