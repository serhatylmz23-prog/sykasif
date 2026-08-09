from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from terminal_v2.core.panel_state import (
    panel_state_store,
)


router = APIRouter(
    prefix="/api/v2/panel",
    tags=["Terminal V2 Live Panel"],
)


class PanelStateUpdate(BaseModel):
    patch: dict[str, Any]


class PanelEventRequest(BaseModel):
    event_type: str = Field(
        min_length=2,
        max_length=120,
    )
    source: str = Field(
        min_length=2,
        max_length=120,
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
    )


@router.get("/state")
async def panel_state() -> dict[str, Any]:
    return await panel_state_store.snapshot()


@router.post("/state")
async def update_panel_state(
    request: PanelStateUpdate,
) -> dict[str, Any]:
    return await panel_state_store.update(
        request.patch
    )


@router.post("/event")
async def publish_panel_event(
    request: PanelEventRequest,
) -> dict[str, Any]:
    return await panel_state_store.record_event(
        event_type=request.event_type,
        source=request.source,
        payload=request.payload,
    )


@router.delete("/state")
async def reset_panel_state() -> dict[str, Any]:
    return await panel_state_store.reset()
