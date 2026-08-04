"""Merkezi çalışma olayı dağıtım sistemi."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from .enums import RuntimeEventPriority


class RuntimeEventHandlerError(RuntimeError):
    """Olay işleyici hatası."""


@dataclass(slots=True, frozen=True)
class RuntimeEvent:
    topic: str
    source: str
    payload: dict[str, Any] = field(
        default_factory=dict
    )
    priority: RuntimeEventPriority = (
        RuntimeEventPriority.NORMAL
    )
    event_id: str = field(
        default_factory=lambda: (
            "SYK-EVT-" + uuid4().hex.upper()
        )
    )
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("Olay başlığı boş olamaz.")

        if not self.source.strip():
            raise ValueError("Olay kaynağı boş olamaz.")


RuntimeEventHandler = Callable[[RuntimeEvent], None]


class RuntimeEventBus:
    def __init__(self) -> None:
        self._handlers: dict[
            str,
            list[RuntimeEventHandler],
        ] = defaultdict(list)

        self._history: list[RuntimeEvent] = []
        self._handler_errors: list[str] = []
        self._lock = RLock()

    def subscribe(
        self,
        topic: str,
        handler: RuntimeEventHandler,
    ) -> None:
        if not topic.strip():
            raise ValueError(
                "Abonelik başlığı boş olamaz."
            )

        with self._lock:
            if handler not in self._handlers[topic]:
                self._handlers[topic].append(handler)

    def unsubscribe(
        self,
        topic: str,
        handler: RuntimeEventHandler,
    ) -> None:
        with self._lock:
            if handler in self._handlers.get(topic, []):
                self._handlers[topic].remove(handler)

    def publish(
        self,
        event: RuntimeEvent,
        *,
        raise_handler_error: bool = False,
    ) -> int:
        with self._lock:
            self._history.append(event)

            handlers = tuple(
                self._handlers.get(event.topic, [])
            ) + tuple(
                self._handlers.get("*", [])
            )

        successful_handler_count = 0

        for handler in handlers:
            try:
                handler(event)
                successful_handler_count += 1
            except Exception as exc:
                error_text = (
                    f"{event.event_id}:"
                    f"{type(exc).__name__}:{exc}"
                )

                with self._lock:
                    self._handler_errors.append(
                        error_text
                    )

                if raise_handler_error:
                    raise RuntimeEventHandlerError(
                        error_text
                    ) from exc

        return successful_handler_count

    @property
    def history(
        self,
    ) -> tuple[RuntimeEvent, ...]:
        with self._lock:
            return tuple(self._history)

    @property
    def handler_errors(
        self,
    ) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._handler_errors)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "event_count": len(self._history),
                "handler_error_count": len(
                    self._handler_errors
                ),
                "subscription_count": sum(
                    len(handlers)
                    for handlers in self._handlers.values()
                ),
                "topics": sorted(self._handlers),
            }
