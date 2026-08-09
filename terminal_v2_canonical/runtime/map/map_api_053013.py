from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .map_state_service import map_state_service


router = APIRouter(
    prefix="/api/v2/map",
    tags=["SyKaşif Harita"],
)


class LayerSelection(BaseModel):
    id: str | None = None
    title: str
    category: str = "dinamik"
    priority: int = 50
    heavy: bool = False


class SelectionRequest(BaseModel):
    selected: list[LayerSelection] = Field(
        default_factory=list
    )


class ViewportRequest(BaseModel):
    latitude: float
    longitude: float
    zoom: float | None = None


class ModeRequest(BaseModel):
    mode: str


@router.get("/state")
def map_state() -> dict[str, Any]:
    return map_state_service.snapshot()


@router.post("/selection")
def map_selection(
    body: SelectionRequest,
) -> dict[str, Any]:
    return map_state_service.sync_selection(
        [
            item.model_dump()
            for item in body.selected
        ]
    )


@router.post("/viewport")
def map_viewport(
    body: ViewportRequest,
) -> dict[str, Any]:
    return map_state_service.set_viewport(
        latitude=body.latitude,
        longitude=body.longitude,
        zoom=body.zoom,
    )


@router.post("/mode")
def map_mode(
    body: ModeRequest,
) -> dict[str, Any]:
    return map_state_service.set_mode(
        body.mode
    )
