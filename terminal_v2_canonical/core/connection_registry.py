from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(UTC)


def detect_device(
    user_agent: str,
) -> str:
    value = user_agent.lower()

    tablet_tokens = (
        "tablet",
        "ipad",
        "android",
        "sm-x",
        "tab",
    )

    if any(token in value for token in tablet_tokens):
        return "tablet"

    mobile_tokens = (
        "mobile",
        "iphone",
    )

    if any(token in value for token in mobile_tokens):
        return "mobile"

    return "desktop"


@dataclass(slots=True)
class StreamClient:
    client_id: str
    host: str
    user_agent: str
    device_type: str
    connected_at: datetime
    last_event_at: datetime
    event_count: int = 0

    def export(self) -> dict[str, Any]:
        data = asdict(self)

        data["connected_at"] = self.connected_at.isoformat()
        data["last_event_at"] = self.last_event_at.isoformat()

        return data


class ConnectionRegistry:
    def __init__(
        self,
        *,
        stale_after_seconds: float = 20.0,
    ) -> None:
        self._clients: dict[str, StreamClient] = {}
        self._lock = asyncio.Lock()
        self._total_connections = 0
        self._total_events = 0
        self._total_disconnections = 0
        self._total_stale_removed = 0
        self._stale_after_seconds = stale_after_seconds

    async def connect(
        self,
        *,
        host: str,
        user_agent: str,
    ) -> StreamClient:
        now = utc_now()

        client = StreamClient(
            client_id=str(uuid4()),
            host=host or "unknown",
            user_agent=user_agent or "unknown",
            device_type=detect_device(user_agent),
            connected_at=now,
            last_event_at=now,
        )

        async with self._lock:
            self._clients[client.client_id] = client
            self._total_connections += 1

        return client

    async def disconnect(
        self,
        client_id: str,
    ) -> bool:
        async with self._lock:
            removed = self._clients.pop(
                client_id,
                None,
            )

            if removed is None:
                return False

            self._total_disconnections += 1

            return True

    async def record_event(
        self,
        client_id: str,
    ) -> bool:
        async with self._lock:
            client = self._clients.get(client_id)

            if client is None:
                return False

            client.event_count += 1
            client.last_event_at = utc_now()
            self._total_events += 1

            return True

    async def remove_stale(
        self,
        *,
        now: datetime | None = None,
    ) -> list[str]:
        current = now or utc_now()

        threshold = current - timedelta(
            seconds=self._stale_after_seconds,
        )

        async with self._lock:
            stale_ids = [
                client_id
                for client_id, client in self._clients.items()
                if client.last_event_at < threshold
            ]

            for client_id in stale_ids:
                self._clients.pop(
                    client_id,
                    None,
                )

            self._total_stale_removed += len(stale_ids)

            return stale_ids

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            clients = [
                client.export()
                for client in self._clients.values()
            ]

            clients.sort(
                key=lambda item: item["connected_at"],
            )

            device_counts = {
                "desktop": 0,
                "tablet": 0,
                "mobile": 0,
            }

            for client in clients:
                device_type = client["device_type"]

                device_counts[device_type] = (
                    device_counts.get(
                        device_type,
                        0,
                    )
                    + 1
                )

            return {
                "active_connections": len(clients),
                "active_desktop": device_counts["desktop"],
                "active_tablet": device_counts["tablet"],
                "active_mobile": device_counts["mobile"],
                "total_connections": self._total_connections,
                "total_disconnections": self._total_disconnections,
                "total_events": self._total_events,
                "total_stale_removed": self._total_stale_removed,
                "stale_after_seconds": self._stale_after_seconds,
                "clients": clients,
                "timestamp": utc_now().isoformat(),
            }

    async def reset(self) -> None:
        async with self._lock:
            self._clients.clear()
            self._total_connections = 0
            self._total_disconnections = 0
            self._total_events = 0
            self._total_stale_removed = 0


registry = ConnectionRegistry()
