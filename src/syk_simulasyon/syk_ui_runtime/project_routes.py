from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from .project_runtime import project_repository


class ProjectCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=160,
    )
    research_area: str = Field(
        min_length=1,
        max_length=240,
    )
    description: str = Field(
        default="",
        max_length=2000,
    )


project_router = APIRouter(
    prefix="/api/syk-ui/projects",
    tags=["syk-ui-projects"],
)


@project_router.get("")
def list_projects() -> dict[str, object]:
    projects = [
        project.to_dict()
        for project in project_repository.list()
    ]

    active_project_id = next(
        (
            project["project_id"]
            for project in projects
            if project["active"]
        ),
        None,
    )

    return {
        "count": len(projects),
        "active_project_id": active_project_id,
        "projects": projects,
    }


@project_router.post(
    "",
    status_code=201,
)
def create_project(
    request: ProjectCreateRequest,
) -> dict[str, object]:
    try:
        project = project_repository.create(
            name=request.name,
            research_area=request.research_area,
            description=request.description,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return project.to_dict()


@project_router.get("/{project_id}")
def get_project(
    project_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    project = project_repository.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Proje bulunamadı.",
        )

    return project.to_dict()


@project_router.patch("/{project_id}/activate")
def activate_project(
    project_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    project = project_repository.activate(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Proje bulunamadı.",
        )

    return project.to_dict()


@project_router.patch("/{project_id}/archive")
def archive_project(
    project_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    project = project_repository.archive(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Proje bulunamadı.",
        )

    return project.to_dict()