from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class PanelStateStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._revision = 0
        self._state: dict[str, Any] = {
            "runtime": {
                "status": "ONLINE",
            },
            "active_module": "dashboard",
            "panels": {
                "desktop": True,
                "tablet": False,
                "phone": False,
            },
            "modules": {},
            "notifications": [],
            "last_event": None,
            "updated_at": utc_now(),
        }

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            return {
                "revision": self._revision,
                "state": deepcopy(self._state),
            }

    async def update(
        self,
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        async with self._lock:
            self._merge(
                self._state,
                patch,
            )

            self._revision += 1
            self._state["updated_at"] = utc_now()

            return {
                "revision": self._revision,
                "state": deepcopy(self._state),
            }

    async def record_event(
        self,
        *,
        event_type: str,
        source: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        async with self._lock:
            self._revision += 1

            event = {
                "revision": self._revision,
                "type": event_type,
                "source": source,
                "payload": deepcopy(payload),
                "timestamp": utc_now(),
            }

            self._state["last_event"] = event
            self._state["updated_at"] = event["timestamp"]

            return {
                "revision": self._revision,
                "event": deepcopy(event),
                "state": deepcopy(self._state),
            }

    async def reset(self) -> dict[str, Any]:
        async with self._lock:
            self._revision = 0

            self._state = {
                "runtime": {
                    "status": "ONLINE",
                },
                "active_module": "dashboard",
                "panels": {
                    "desktop": True,
                    "tablet": False,
                    "phone": False,
                },
                "modules": {},
                "notifications": [],
                "last_event": None,
                "updated_at": utc_now(),
            }

            return {
                "revision": self._revision,
                "state": deepcopy(self._state),
            }

    @classmethod
    def _merge(
        cls,
        target: dict[str, Any],
        patch: dict[str, Any],
    ) -> None:
        for key, value in patch.items():
            if (
                isinstance(value, dict)
                and isinstance(target.get(key), dict)
            ):
                cls._merge(
                    target[key],
                    value,
                )
            else:
                target[key] = deepcopy(value)


panel_state_store = PanelStateStore()
