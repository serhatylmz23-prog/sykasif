from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class PanelBroadcastHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._clients: set[
            asyncio.Queue[dict[str, Any]]
        ] = set()

    async def connect(
        self,
    ) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[
            dict[str, Any]
        ] = asyncio.Queue(maxsize=64)

        async with self._lock:
            self._clients.add(queue)

        return queue

    async def disconnect(
        self,
        queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        async with self._lock:
            self._clients.discard(queue)

    async def publish(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event = {
            "type": event_type,
            "payload": deepcopy(payload),
            "timestamp": utc_now(),
        }

        async with self._lock:
            clients = tuple(self._clients)

        for queue in clients:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

        return event

    async def client_count(self) -> int:
        async with self._lock:
            return len(self._clients)


async def sse_stream(
    queue: asyncio.Queue[dict[str, Any]],
) -> AsyncIterator[str]:
    yield (
        "event: baglanti\n"
        "data: "
        + json.dumps(
            {
                "durum": "BAGLANDI",
                "mesaj": (
                    "Canlı panel bağlantısı kuruldu."
                ),
                "timestamp": utc_now(),
            },
            ensure_ascii=False,
        )
        + "\n\n"
    )

    while True:
        try:
            event = await asyncio.wait_for(
                queue.get(),
                timeout=15.0,
            )

            yield (
                f"event: {event['type']}\n"
                "data: "
                + json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        except TimeoutError:
            yield (
                "event: nabiz\n"
                "data: "
                + json.dumps(
                    {
                        "durum": "CANLI",
                        "mesaj": (
                            "Canlı panel bağlantısı aktif."
                        ),
                        "timestamp": utc_now(),
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )


panel_broadcast_hub = PanelBroadcastHub()
