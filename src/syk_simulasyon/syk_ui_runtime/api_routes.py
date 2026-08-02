from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .module_registry import enabled_modules
from .scientific_runtime import ScientificRuntime
from .ui_runtime_state import UIRuntimeState


router = APIRouter(
    prefix="/api/syk-ui",
    tags=["syk-ui"],
)

runtime_state = UIRuntimeState()
scientific_runtime = ScientificRuntime()


@router.get("/runtime-state")
def get_runtime_state() -> dict:
    snapshot = runtime_state.snapshot()
    snapshot["modules"] = [
        {
            "id": module.id,
            "title": module.title,
            "enabled": module.enabled,
        }
        for module in enabled_modules()
    ]
    return snapshot


@router.websocket("/live")
async def live_runtime(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while True:
            snapshot = get_runtime_state()
            snapshot["connection"] = "live"

            await websocket.send_json(snapshot)
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        return

@router.get("/scientific-modules")
def get_scientific_modules() -> list[dict]:
    return scientific_runtime.inventory()


@router.get("/scientific-modules/{module_id}")
def get_scientific_module(module_id: str) -> dict:
    try:
        return scientific_runtime.get(module_id)
    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Unknown scientific module: {module_id}",
        ) from error

class ScientificUpdateRequest(BaseModel):
    live_value: float | int | str | None = None
    confidence: float | None = None
    status: str | None = None
    source: str | None = None


@router.patch("/scientific-modules/{module_id}")
def update_scientific_module(
    module_id: str,
    request: ScientificUpdateRequest,
) -> dict:
    try:
        return scientific_runtime.update(
            module_id,
            live_value=request.live_value,
            confidence=request.confidence,
            status=request.status,
            source=request.source,
        )
    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Unknown scientific module: {module_id}",
        ) from error


@router.websocket(
    "/scientific-modules/{module_id}/live"
)
async def scientific_module_live(
    websocket: WebSocket,
    module_id: str,
) -> None:
    if not scientific_runtime.exists(module_id):
        await websocket.close(
            code=4404,
            reason="Unknown scientific module",
        )
        return

    await websocket.accept()

    try:
        last_sequence = -1

        while True:
            payload = scientific_runtime.get(module_id)
            sequence = payload["state"]["sequence"]

            if sequence != last_sequence:
                await websocket.send_json(payload)
                last_sequence = sequence

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        return