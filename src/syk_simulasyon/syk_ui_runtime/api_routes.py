from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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