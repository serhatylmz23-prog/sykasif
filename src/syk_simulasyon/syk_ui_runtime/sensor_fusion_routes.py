from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
)
from pydantic import BaseModel, Field

from .sensor_fusion_runtime import (
    FusionRule,
    sensor_fusion_runtime,
)


class FusionRequest(BaseModel):
    research_id: str | None = Field(
        default=None,
        max_length=180,
    )
    workspace_id: str | None = Field(
        default=None,
        max_length=180,
    )
    time_tolerance_seconds: float = Field(
        default=5.0,
        ge=0.0,
        le=3600.0,
    )
    location_tolerance_m: float = Field(
        default=15.0,
        ge=0.0,
        le=100000.0,
    )
    minimum_source_count: int = Field(
        default=2,
        ge=1,
        le=64,
    )
    minimum_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )
    source_weights: dict[
        str,
        float,
    ] = Field(
        default_factory=dict
    )


sensor_fusion_router = APIRouter(
    prefix="/api/syk-ui/sensor-fusion",
    tags=["syk-ui-sensor-fusion"],
)


@sensor_fusion_router.get("")
def list_groups(
    research_id: Annotated[
        str | None,
        Query(),
    ] = None,
    workspace_id: Annotated[
        str | None,
        Query(),
    ] = None,
) -> dict[str, object]:
    groups = sensor_fusion_runtime.list(
        research_id=research_id,
        workspace_id=workspace_id,
    )

    return {
        "count": len(groups),
        "groups": [
            group.to_dict()
            for group in groups
        ],
    }


@sensor_fusion_router.post(
    "/run",
    status_code=201,
)
def run_fusion(
    request: FusionRequest,
) -> dict[str, object]:
    try:
        groups = sensor_fusion_runtime.fuse(
            research_id=request.research_id,
            workspace_id=request.workspace_id,
            rule=FusionRule(
                time_tolerance_seconds=(
                    request.time_tolerance_seconds
                ),
                location_tolerance_m=(
                    request.location_tolerance_m
                ),
                minimum_source_count=(
                    request.minimum_source_count
                ),
                minimum_confidence=(
                    request.minimum_confidence
                ),
            ),
            source_weights=(
                request.source_weights
            ),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "count": len(groups),
        "groups": [
            group.to_dict()
            for group in groups
        ],
    }


@sensor_fusion_router.get(
    "/{group_id}"
)
def get_group(
    group_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    group = sensor_fusion_runtime.get(
        group_id
    )

    if group is None:
        raise HTTPException(
            status_code=404,
            detail="Sensör birleşim grubu bulunamadı.",
        )

    return group.to_dict()