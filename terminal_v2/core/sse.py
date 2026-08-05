from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from itertools import count
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from terminal_v2.core.connection_registry import registry


router = APIRouter(
    prefix="/api/v2",
    tags=["Terminal V2 SSE"],
)

_event_ids = count(1)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def encode_sse(
    *,
    event: str,
    data: dict[str, Any],
    event_id: int | None = None,
    retry: int | None = None,
) -> str:
    lines: list[str] = []

    if event_id is not None:
        lines.append(f"id: {event_id}")

    if retry is not None:
        lines.append(f"retry: {retry}")

    lines.append(f"event: {event}")

    payload = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    for line in payload.splitlines() or [""]:
        lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"


def initial_snapshot(
    *,
    client_id: str | None = None,
    device_type: str | None = None,
) -> dict[str, Any]:
    return {
        "type": "snapshot",
        "terminal": "v2",
        "runtime": "ONLINE",
        "port": 8013,
        "stream": "ONLINE",
        "transport": "SSE",
        "client_id": client_id,
        "device_type": device_type,
        "timestamp": utc_now(),
    }


def heartbeat_snapshot(
    *,
    client_id: str | None = None,
    device_type: str | None = None,
) -> dict[str, Any]:
    return {
        "type": "heartbeat",
        "runtime": "ONLINE",
        "stream": "ONLINE",
        "client_id": client_id,
        "device_type": device_type,
        "timestamp": utc_now(),
    }


async def metrics_snapshot() -> dict[str, Any]:
    snapshot = await registry.snapshot()

    return {
        "type": "metrics",
        "runtime": "ONLINE",
        "stream": "ONLINE",
        "active_connections": snapshot["active_connections"],
        "active_tablet": snapshot["active_tablet"],
        "active_desktop": snapshot["active_desktop"],
        "active_mobile": snapshot["active_mobile"],
        "total_connections": snapshot["total_connections"],
        "total_events": snapshot["total_events"],
        "timestamp": utc_now(),
    }


async def event_stream(
    request: Request,
) -> AsyncIterator[str]:
    client_host = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    client = await registry.connect(
        host=client_host,
        user_agent=request.headers.get(
            "user-agent",
            "unknown",
        ),
    )

    try:
        await registry.record_event(client.client_id)

        yield encode_sse(
            event="terminal.snapshot",
            event_id=next(_event_ids),
            retry=2000,
            data=initial_snapshot(
                client_id=client.client_id,
                device_type=client.device_type,
            ),
        )

        yield encode_sse(
            event="terminal.metrics",
            event_id=next(_event_ids),
            data=await metrics_snapshot(),
        )

        heartbeat_seconds = 5.0

        while True:
            if await request.is_disconnected():
                break

            await asyncio.sleep(heartbeat_seconds)

            if await request.is_disconnected():
                break

            await registry.remove_stale()

            recorded = await registry.record_event(
                client.client_id,
            )

            if not recorded:
                break

            yield encode_sse(
                event="terminal.heartbeat",
                event_id=next(_event_ids),
                data=heartbeat_snapshot(
                    client_id=client.client_id,
                    device_type=client.device_type,
                ),
            )

            yield encode_sse(
                event="terminal.metrics",
                event_id=next(_event_ids),
                data=await metrics_snapshot(),
            )
    finally:
        await registry.disconnect(
            client.client_id,
        )


@router.get("/events")
async def events(
    request: Request,
) -> StreamingResponse:
    return StreamingResponse(
        event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/events/snapshot")
def events_snapshot() -> dict[str, Any]:
    return initial_snapshot()


@router.get("/events/metrics")
async def events_metrics() -> dict[str, Any]:
    await registry.remove_stale()

    return await metrics_snapshot()


@router.get("/connections")
async def connections() -> dict[str, Any]:
    await registry.remove_stale()

    return await registry.snapshot()


@router.post("/connections/cleanup")
async def cleanup_connections() -> dict[str, Any]:
    removed = await registry.remove_stale()
    snapshot = await registry.snapshot()

    return {
        "removed_count": len(removed),
        "removed_client_ids": removed,
        "active_connections": snapshot[
            "active_connections"
        ],
        "timestamp": utc_now(),
    }
