from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.project_routes import (
    project_router,
)
from syk_simulasyon.syk_ui_runtime.project_runtime import (
    project_repository,
)


def client() -> TestClient:
    project_repository.reset()

    app = FastAPI()
    app.include_router(project_router)

    return TestClient(app)


def test_project_create_list_activate_archive() -> None:
    test_client = client()

    first_response = test_client.post(
        "/api/syk-ui/projects",
        json={
            "name": "Keban Araştırması",
            "research_area": "Harita ve sonar",
            "description": "İlk saha projesi",
        },
    )

    assert first_response.status_code == 201

    first = first_response.json()

    second_response = test_client.post(
        "/api/syk-ui/projects",
        json={
            "name": "Jeoloji İncelemesi",
            "research_area": "Jeoloji",
        },
    )

    assert second_response.status_code == 201

    second = second_response.json()

    list_response = test_client.get(
        "/api/syk-ui/projects"
    )

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 2

    activate_response = test_client.patch(
        f"/api/syk-ui/projects/{second['project_id']}/activate"
    )

    assert activate_response.status_code == 200
    assert activate_response.json()["active"] is True

    refreshed_first = test_client.get(
        f"/api/syk-ui/projects/{first['project_id']}"
    ).json()

    assert refreshed_first["active"] is False

    archive_response = test_client.patch(
        f"/api/syk-ui/projects/{second['project_id']}/archive"
    )

    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"
    assert archive_response.json()["active"] is False


def test_project_validation_and_not_found() -> None:
    test_client = client()

    invalid_response = test_client.post(
        "/api/syk-ui/projects",
        json={
            "name": "",
            "research_area": "",
        },
    )

    assert invalid_response.status_code == 422

    missing_response = test_client.get(
        "/api/syk-ui/projects/bilinmeyen"
    )

    assert missing_response.status_code == 404