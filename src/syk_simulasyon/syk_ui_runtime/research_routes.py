from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from .research_runtime import research_repository


class ResearchCreateRequest(BaseModel):
    project_id: str = Field(
        min_length=1,
        max_length=120,
    )
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    research_type: str = Field(
        min_length=1,
        max_length=120,
    )
    notes: str = Field(
        default="",
        max_length=4000,
    )


class LinkRequest(BaseModel):
    value: str = Field(
        min_length=1,
        max_length=240,
    )


research_router = APIRouter(
    prefix="/api/syk-ui/research",
    tags=["syk-ui-research"],
)


@research_router.get("")
def list_research(
    project_id: Annotated[
        str | None,
        Query(),
    ] = None,
) -> dict[str, object]:
    records = [
        record.to_dict()
        for record in research_repository.list(
            project_id=project_id,
        )
    ]

    return {
        "count": len(records),
        "records": records,
    }


@research_router.post(
    "",
    status_code=201,
)
def create_research(
    request: ResearchCreateRequest,
) -> dict[str, object]:
    try:
        record = research_repository.create(
            project_id=request.project_id,
            title=request.title,
            research_type=request.research_type,
            notes=request.notes,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return record.to_dict()


@research_router.get("/{research_id}")
def get_research(
    research_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    record = research_repository.get(research_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Araştırma kaydı bulunamadı.",
        )

    return record.to_dict()


@research_router.patch("/{research_id}/start")
def start_research(
    research_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    record = research_repository.start(research_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Araştırma kaydı bulunamadı.",
        )

    return record.to_dict()


@research_router.patch("/{research_id}/complete")
def complete_research(
    research_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    record = research_repository.complete(research_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Araştırma kaydı bulunamadı.",
        )

    return record.to_dict()


@research_router.patch("/{research_id}/media")
def link_media(
    research_id: str,
    request: LinkRequest,
) -> dict[str, object]:
    return _link(
        research_id,
        request.value,
        research_repository.add_media,
    )


@research_router.patch("/{research_id}/evidence")
def link_evidence(
    research_id: str,
    request: LinkRequest,
) -> dict[str, object]:
    return _link(
        research_id,
        request.value,
        research_repository.add_evidence,
    )


@research_router.patch("/{research_id}/map-layer")
def link_map_layer(
    research_id: str,
    request: LinkRequest,
) -> dict[str, object]:
    return _link(
        research_id,
        request.value,
        research_repository.add_map_layer,
    )


def _link(
    research_id: str,
    value: str,
    operation,
) -> dict[str, object]:
    try:
        record = operation(
            research_id,
            value,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Araştırma kaydı bulunamadı.",
        )

    return record.to_dict()