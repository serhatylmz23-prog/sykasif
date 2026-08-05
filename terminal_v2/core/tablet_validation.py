from __future__ import annotations

import asyncio
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class TabletValidation:
    token: str
    created_at: datetime
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    client_host: str | None = None
    user_agent: str | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    touch_supported: bool | None = None
    event_source_supported: bool | None = None
    sse_connected: bool = False

    def export(self) -> dict[str, Any]:
        data = asdict(self)

        data["created_at"] = self.created_at.isoformat()

        data["acknowledged_at"] = (
            self.acknowledged_at.isoformat()
            if self.acknowledged_at is not None
            else None
        )

        data["digital_checks_passed"] = (
            self.acknowledged
            and self.sse_connected
            and self.event_source_supported is True
            and self.viewport_width is not None
            and self.viewport_height is not None
        )

        return data


class TabletValidationRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, TabletValidation] = {}
        self._lock = asyncio.Lock()

    async def create(self) -> TabletValidation:
        session = TabletValidation(
            token=secrets.token_urlsafe(24),
            created_at=utc_now(),
        )

        async with self._lock:
            self._sessions[session.token] = session

        return session

    async def get(
        self,
        token: str,
    ) -> TabletValidation | None:
        async with self._lock:
            return self._sessions.get(token)

    async def acknowledge(
        self,
        *,
        token: str,
        client_host: str,
        user_agent: str,
        viewport_width: int,
        viewport_height: int,
        touch_supported: bool,
        event_source_supported: bool,
        sse_connected: bool,
    ) -> TabletValidation | None:
        async with self._lock:
            session = self._sessions.get(token)

            if session is None:
                return None

            session.acknowledged = True
            session.acknowledged_at = utc_now()
            session.client_host = client_host
            session.user_agent = user_agent
            session.viewport_width = viewport_width
            session.viewport_height = viewport_height
            session.touch_supported = touch_supported
            session.event_source_supported = event_source_supported
            session.sse_connected = sse_connected

            return session

    async def reset(
        self,
        token: str,
    ) -> bool:
        async with self._lock:
            return self._sessions.pop(
                token,
                None,
            ) is not None


tablet_validation_registry = TabletValidationRegistry()
