from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.map_workspace_routes import (
    map_workspace_router,
)
from syk_simulasyon.syk_ui_runtime.map_workspace_runtime import (
    map_workspace_repository,
)
from syk_simulasyon.syk_ui_runtime.project_runtime import (
    project_repository,
)
from syk_simulasyon.syk_ui_runtime.research_runtime import (
    research_repository,
)


def client() -> TestClient:
    project_repository.reset()
    research_repository.reset()
    map_workspace_repository.reset()

    app = FastAPI()
    app.include_router(map_workspace_router)

    return TestClient(app)


def create_research() -> str:
    project = project_repository.create(
        name="Keban Harita Projesi",
        research_area="Harita ve sonar",
    )

    research = research_repository.create(
        project_id=project.project_id,
        title="Kıyı Şeridi Araştırması",
        research_type="map-sonar",
    )

    return research.research_id


def test_map_workspace_full_flow() -> None:
    test_client = client()
    research_id = create_research()

    create_response = test_client.post(
        "/api/syk-ui/map-workspaces",
        json={
            "research_id": research_id,
            "name": "Keban Kıyı Alanı",
            "latitude": 38.7123,
            "longitude": 38.4521,
            "zoom": 18,
        },
    )

    assert create_response.status_code == 201

    workspace = create_response.json()
    workspace_id = workspace["workspace_id"]

    assert workspace["status"] == "ready"
    assert len(workspace["layers"]) == 2

    activate_response = test_client.patch(
        f"/api/syk-ui/map-workspaces/{workspace_id}/activate"
    )

    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "active"

    ar_response = test_client.patch(
        f"/api/syk-ui/map-workspaces/{workspace_id}/ar",
        json={"enabled": True},
    )

    assert ar_response.status_code == 200
    assert ar_response.json()["ar_enabled"] is True

    pin_response = test_client.post(
        f"/api/syk-ui/map-workspaces/{workspace_id}/pins",
        json={
            "name": "Kıyı Ölçüm Noktası",
            "latitude": 38.7124,
            "longitude": 38.4522,
            "altitude_m": 845.2,
            "accuracy_m": 1.4,
        },
    )

    assert pin_response.status_code == 201
    assert len(pin_response.json()["pins"]) == 1

    sonar_response = test_client.post(
        f"/api/syk-ui/map-workspaces/{workspace_id}/layers",
        json={
            "key": "garmin-sonar",
            "name": "Garmin Sonar",
            "layer_type": "sonar",
            "opacity": 0.82,
            "ar_enabled": True,
            "source": "external-device-adapter",
            "metadata": {
                "priority_depth_m": 2.0,
                "data_state": "adapter-ready",
            },
        },
    )

    assert sonar_response.status_code == 201

    layers = sonar_response.json()["layers"]

    assert any(
        layer["key"] == "garmin-sonar"
        for layer in layers
    )

    measurement_response = test_client.post(
        (
            f"/api/syk-ui/map-workspaces/"
            f"{workspace_id}/measurements"
        ),
        json={
            "measurement_type": "distance",
            "value": 14.8,
            "unit": "m",
            "start": {
                "latitude": 38.7123,
                "longitude": 38.4521,
            },
            "end": {
                "latitude": 38.7124,
                "longitude": 38.4522,
            },
        },
    )

    assert measurement_response.status_code == 201
    assert len(
        measurement_response.json()["measurements"]
    ) == 1


def test_map_workspace_validation() -> None:
    test_client = client()

    response = test_client.post(
        "/api/syk-ui/map-workspaces",
        json={
            "research_id": "missing",
            "name": "Test",
            "latitude": 91,
            "longitude": 0,
        },
    )

    assert response.status_code in {404, 422}

    missing = test_client.get(
        "/api/syk-ui/map-workspaces/missing"
    )

    assert missing.status_code == 404