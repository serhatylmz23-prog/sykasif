from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from .map_workspace_runtime import (
    map_workspace_repository,
)


class Coordinate(BaseModel):
    latitude: float
    longitude: float


class WorkspaceCreateRequest(BaseModel):
    research_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=180)
    latitude: float
    longitude: float
    zoom: float = Field(default=16.0, ge=1.0, le=24.0)


class ArStateRequest(BaseModel):
    enabled: bool


class PinCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    latitude: float
    longitude: float
    altitude_m: float | None = None
    accuracy_m: float | None = Field(default=None, ge=0)
    note: str = Field(default="", max_length=1000)


class LayerCreateRequest(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    layer_type: str = Field(min_length=1, max_length=100)
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    ar_enabled: bool = False
    source: str = Field(min_length=1, max_length=180)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MeasurementCreateRequest(BaseModel):
    measurement_type: str = Field(
        min_length=1,
        max_length=100,
    )
    value: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=40)
    start: Coordinate
    end: Coordinate | None = None


map_workspace_router = APIRouter(
    prefix="/api/syk-ui/map-workspaces",
    tags=["syk-ui-map-workspaces"],
)


@map_workspace_router.get("")
def list_workspaces(
    research_id: Annotated[
        str | None,
        Query(),
    ] = None,
) -> dict[str, object]:
    workspaces = [
        workspace.to_dict()
        for workspace in map_workspace_repository.list(
            research_id=research_id,
        )
    ]

    return {
        "count": len(workspaces),
        "workspaces": workspaces,
    }


@map_workspace_router.post(
    "",
    status_code=201,
)
def create_workspace(
    request: WorkspaceCreateRequest,
) -> dict[str, object]:
    try:
        workspace = map_workspace_repository.create(
            research_id=request.research_id,
            name=request.name,
            latitude=request.latitude,
            longitude=request.longitude,
            zoom=request.zoom,
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

    return workspace.to_dict()


@map_workspace_router.get("/{workspace_id}")
def get_workspace(
    workspace_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    workspace = map_workspace_repository.get(
        workspace_id
    )

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Harita çalışma alanı bulunamadı.",
        )

    return workspace.to_dict()


@map_workspace_router.patch("/{workspace_id}/activate")
def activate_workspace(
    workspace_id: str,
) -> dict[str, object]:
    return _require(
        map_workspace_repository.activate(
            workspace_id
        )
    )


@map_workspace_router.patch("/{workspace_id}/ar")
def set_ar_state(
    workspace_id: str,
    request: ArStateRequest,
) -> dict[str, object]:
    return _require(
        map_workspace_repository.set_ar(
            workspace_id,
            enabled=request.enabled,
        )
    )


@map_workspace_router.post(
    "/{workspace_id}/pins",
    status_code=201,
)
def add_pin(
    workspace_id: str,
    request: PinCreateRequest,
) -> dict[str, object]:
    try:
        workspace = map_workspace_repository.add_pin(
            workspace_id,
            name=request.name,
            latitude=request.latitude,
            longitude=request.longitude,
            altitude_m=request.altitude_m,
            accuracy_m=request.accuracy_m,
            note=request.note,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return _require(workspace)


@map_workspace_router.post(
    "/{workspace_id}/layers",
    status_code=201,
)
def add_layer(
    workspace_id: str,
    request: LayerCreateRequest,
) -> dict[str, object]:
    try:
        workspace = map_workspace_repository.add_layer(
            workspace_id,
            key=request.key,
            name=request.name,
            layer_type=request.layer_type,
            opacity=request.opacity,
            ar_enabled=request.ar_enabled,
            source=request.source,
            metadata=request.metadata,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return _require(workspace)


@map_workspace_router.post(
    "/{workspace_id}/measurements",
    status_code=201,
)
def add_measurement(
    workspace_id: str,
    request: MeasurementCreateRequest,
) -> dict[str, object]:
    try:
        workspace = (
            map_workspace_repository.add_measurement(
                workspace_id,
                measurement_type=request.measurement_type,
                value=request.value,
                unit=request.unit,
                start=request.start.model_dump(),
                end=(
                    request.end.model_dump()
                    if request.end is not None
                    else None
                ),
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return _require(workspace)


def _require(workspace):
    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Harita çalışma alanı bulunamadı.",
        )

    return workspace.to_dict()