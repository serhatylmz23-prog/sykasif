from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.project_runtime import (
    project_repository,
)
from syk_simulasyon.syk_ui_runtime.research_routes import (
    research_router,
)
from syk_simulasyon.syk_ui_runtime.research_runtime import (
    research_repository,
)


def client() -> TestClient:
    project_repository.reset()
    research_repository.reset()

    app = FastAPI()
    app.include_router(research_router)

    return TestClient(app)


def test_research_full_flow() -> None:
    test_client = client()

    project = project_repository.create(
        name="Keban Çalışması",
        research_area="Harita ve sonar",
    )

    create_response = test_client.post(
        "/api/syk-ui/research",
        json={
            "project_id": project.project_id,
            "title": "Kıyı Alanı İncelemesi",
            "research_type": "harita",
            "notes": "İlk araştırma kaydı",
        },
    )

    assert create_response.status_code == 201

    research = create_response.json()
    research_id = research["research_id"]

    assert research["project_id"] == project.project_id
    assert research["status"] == "ready"

    start_response = test_client.patch(
        f"/api/syk-ui/research/{research_id}/start"
    )

    assert start_response.status_code == 200
    assert start_response.json()["status"] == "active"

    media_response = test_client.patch(
        f"/api/syk-ui/research/{research_id}/media",
        json={"value": "media-001"},
    )

    assert media_response.status_code == 200
    assert media_response.json()["media_ids"] == ["media-001"]

    evidence_response = test_client.patch(
        f"/api/syk-ui/research/{research_id}/evidence",
        json={"value": "evidence-001"},
    )

    assert evidence_response.status_code == 200
    assert evidence_response.json()["evidence_ids"] == [
        "evidence-001"
    ]

    map_response = test_client.patch(
        f"/api/syk-ui/research/{research_id}/map-layer",
        json={"value": "topography"},
    )

    assert map_response.status_code == 200
    assert map_response.json()["map_layers"] == ["topography"]

    complete_response = test_client.patch(
        f"/api/syk-ui/research/{research_id}/complete"
    )

    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"

    list_response = test_client.get(
        "/api/syk-ui/research",
        params={"project_id": project.project_id},
    )

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1


def test_research_missing_project_and_record() -> None:
    test_client = client()

    missing_project = test_client.post(
        "/api/syk-ui/research",
        json={
            "project_id": "missing",
            "title": "Test",
            "research_type": "map",
        },
    )

    assert missing_project.status_code == 404

    missing_record = test_client.get(
        "/api/syk-ui/research/missing"
    )

    assert missing_record.status_code == 404