from __future__ import annotations

import asyncio
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from .dtse_attention_engine import (
    AttentionSignal,
    DTSEAttentionEngine,
    NormalizedBox,
)


router = APIRouter(
    prefix="/dtse",
    tags=["dtse"],
)

dtse_attention_engine = DTSEAttentionEngine()


class NormalizedBoxRequest(BaseModel):
    x: float
    y: float
    width: float
    height: float


class AttentionSignalRequest(BaseModel):
    label: str
    kind: str
    confidence: float = Field(
        ge=0.0,
        le=99.9,
    )
    box: NormalizedBoxRequest
    description: str = ""
    metrics: dict[str, Any] = {}
    evidence_refs: list[str] = []


class DTSEFrameRequest(BaseModel):
    media_id: str
    source_kind: str
    frame_index: int = Field(ge=0)
    timestamp_ms: int = Field(ge=0)
    frame_width: int = Field(gt=0)
    frame_height: int = Field(gt=0)
    signals: list[AttentionSignalRequest]


@router.post("/frames/attention")
def ingest_dtse_attention_frame(
    request: DTSEFrameRequest,
) -> dict:
    try:
        signals = [
            AttentionSignal(
                label=signal.label,
                kind=signal.kind,
                confidence=signal.confidence,
                box=NormalizedBox(
                    x=signal.box.x,
                    y=signal.box.y,
                    width=signal.box.width,
                    height=signal.box.height,
                ),
                description=signal.description,
                metrics=signal.metrics,
                evidence_refs=signal.evidence_refs,
            )
            for signal in request.signals
        ]

        return dtse_attention_engine.ingest(
            media_id=request.media_id,
            source_kind=request.source_kind,
            frame_index=request.frame_index,
            timestamp_ms=request.timestamp_ms,
            frame_width=request.frame_width,
            frame_height=request.frame_height,
            signals=signals,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/events")
def get_dtse_attention_events(
    media_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    return dtse_attention_engine.inventory(
        media_id=media_id,
        limit=max(
            1,
            min(500, limit),
        ),
    )


@router.get("/events/{event_id}")
def get_dtse_attention_event(
    event_id: str,
) -> dict:
    try:
        return dtse_attention_engine.get(
            event_id
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=(
                f"DTSE dikkat olayı bulunamadı: "
                f"{event_id}"
            ),
        ) from error


@router.get("/state")
def get_dtse_attention_state() -> dict:
    return dtse_attention_engine.snapshot()


@router.websocket("/live")
async def dtse_attention_live(
    websocket: WebSocket,
) -> None:
    await websocket.accept()
    last_sequence = -1

    try:
        while True:
            snapshot = (
                dtse_attention_engine.snapshot()
            )

            if (
                snapshot["sequence"]
                != last_sequence
            ):
                await websocket.send_json(
                    snapshot
                )
                last_sequence = snapshot[
                    "sequence"
                ]

            await asyncio.sleep(0.25)

    except WebSocketDisconnect:
        return