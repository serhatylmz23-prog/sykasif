from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from terminal_v2.core.panel_broadcast import (
    panel_broadcast_hub,
    sse_stream,
)
from terminal_v2.core.panel_state import (
    panel_state_store,
)


router = APIRouter(
    prefix="/api/v2/panel",
    tags=["Terminal V2 Canlı Panel Yayını"],
)


class PanelBroadcastRequest(BaseModel):
    olay_turu: str = Field(
        min_length=2,
        max_length=120,
    )
    kaynak: str = Field(
        min_length=2,
        max_length=120,
    )
    veri: dict[str, Any] = Field(
        default_factory=dict,
    )


@router.get("/events")
async def panel_events(
    request: Request,
) -> StreamingResponse:
    queue = await panel_broadcast_hub.connect()

    async def stream():
        try:
            async for item in sse_stream(queue):
                if await request.is_disconnected():
                    break

                yield item
        finally:
            await panel_broadcast_hub.disconnect(
                queue
            )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/broadcast")
async def broadcast_panel_event(
    payload: PanelBroadcastRequest,
) -> dict[str, Any]:
    state_result = (
        await panel_state_store.record_event(
            event_type=payload.olay_turu,
            source=payload.kaynak,
            payload=payload.veri,
        )
    )

    event = await panel_broadcast_hub.publish(
        event_type="panel_guncellendi",
        payload={
            "mesaj": (
                "Ortak canlı panel durumu "
                "güncellendi."
            ),
            "revision": state_result["revision"],
            "olay": state_result["event"],
            "durum": state_result["state"],
        },
    )

    return {
        "sonuc": "YAYINLANDI",
        "mesaj": (
            "Canlı panel değişikliği "
            "tüm bağlı cihazlara gönderildi."
        ),
        "revision": state_result["revision"],
        "event": event,
        "bagli_istemci_sayisi": (
            await panel_broadcast_hub.client_count()
        ),
    }


@router.get("/broadcast/status")
async def panel_broadcast_status() -> dict[str, Any]:
    return {
        "durum": "AKTIF",
        "mesaj": "Canlı panel yayını hazır.",
        "bagli_istemci_sayisi": (
            await panel_broadcast_hub.client_count()
        ),
    }
