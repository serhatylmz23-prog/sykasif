from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .module_registry import enabled_modules
from .ui_runtime_state import UIRuntimeState


router = APIRouter(
    prefix="/api/syk-ui",
    tags=["syk-ui"],
)

runtime_state = UIRuntimeState()


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