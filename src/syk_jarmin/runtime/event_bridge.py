from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any
from uuid import uuid4

from syk_jarmin.runtime.notification_router import (
    NotificationRouter,
)


@dataclass(frozen=True, slots=True)
class JarminBridgeEvent:
    event_id: str
    event_type: str
    source: str
    title: str
    message: str
    payload: dict[str, Any]
    notification: dict[str, Any] | None
    created_at: str
    event_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": (
                self.event_type
            ),
            "source": self.source,
            "title": self.title,
            "message": self.message,
            "payload": dict(
                self.payload
            ),
            "notification": (
                self.notification
            ),
            "created_at": self.created_at,
            "event_sha256": (
                self.event_sha256
            ),
        }


class JarminEventBridge:
    EVENT_TITLES = {
        "dtse_attention": (
            "Dikkat Bölgesi Algılandı"
        ),
        "dtse_evidence": (
            "DTSE Kanıtı Oluşturuldu"
        ),
        "analysis_completed": (
            "Analiz Tamamlandı"
        ),
        "report_created": (
            "Mühürlü Rapor Hazır"
        ),
        "theme_changed": (
            "Tema Değiştirildi"
        ),
        "environment_changed": (
            "Ortam Görünümü Güncellendi"
        ),
        "device_disconnected": (
            "Cihaz Bağlantısı Kesildi"
        ),
        "critical_event": (
            "Kritik Olay Algılandı"
        ),
    }

    NOTIFICATION_EVENTS = {
        "dtse_attention",
        "dtse_evidence",
        "analysis_completed",
        "report_created",
        "device_disconnected",
        "critical_event",
    }

    def __init__(
        self,
        notification_router: (
            NotificationRouter | None
        ) = None,
        *,
        maximum_events: int = 500,
    ) -> None:
        if maximum_events <= 0:
            raise ValueError(
                "Azami olay sayısı pozitif "
                "olmalıdır."
            )

        self.notifications = (
            notification_router
            or NotificationRouter()
        )

        self.maximum_events = (
            maximum_events
        )

        self._events: dict[
            str,
            JarminBridgeEvent,
        ] = {}

        self._order: list[str] = []
        self._lock = RLock()

    def publish(
        self,
        *,
        event_type: str,
        source: str,
        message: str,
        payload: dict[str, Any] | None = None,
        title: str | None = None,
    ) -> JarminBridgeEvent:
        normalized_type = (
            event_type.strip().lower()
        )

        normalized_source = (
            source.strip()
        )

        normalized_message = (
            message.strip()
        )

        if not normalized_type:
            raise ValueError(
                "Olay türü boş olamaz."
            )

        if not normalized_source:
            raise ValueError(
                "Olay kaynağı boş olamaz."
            )

        if not normalized_message:
            raise ValueError(
                "Olay mesajı boş olamaz."
            )

        event_id = (
            f"JEV-{uuid4().hex[:24]}"
        )

        created_at = datetime.now(
            UTC
        ).isoformat()

        resolved_title = (
            title.strip()
            if title
            else self.EVENT_TITLES.get(
                normalized_type,
                "Jarmin Olayı",
            )
        )

        event_payload = dict(
            payload or {}
        )

        notification = None

        if (
            normalized_type
            in self.NOTIFICATION_EVENTS
        ):
            notification_event = (
                "critical_event"
                if normalized_type
                == "critical_event"
                else (
                    "device_disconnected"
                    if normalized_type
                    == "device_disconnected"
                    else (
                        "analysis_completed"
                        if normalized_type
                        in {
                            "analysis_completed",
                            "report_created",
                        }
                        else "evidence_created"
                    )
                )
            )

            notification = (
                self.notifications.route(
                    event_type=(
                        notification_event
                    ),
                    message=(
                        normalized_message
                    ),
                )
                .as_dict()
            )

        unsigned = {
            "event_id": event_id,
            "event_type": (
                normalized_type
            ),
            "source": normalized_source,
            "title": resolved_title,
            "message": normalized_message,
            "payload": event_payload,
            "notification": notification,
            "created_at": created_at,
        }

        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        event = JarminBridgeEvent(
            **unsigned,
            event_sha256=sha256(
                canonical
            ).hexdigest(),
        )

        with self._lock:
            self._events[
                event_id
            ] = event

            self._order.append(
                event_id
            )

            overflow = (
                len(self._order)
                - self.maximum_events
            )

            if overflow > 0:
                expired = self._order[
                    :overflow
                ]

                del self._order[
                    :overflow
                ]

                for expired_id in expired:
                    self._events.pop(
                        expired_id,
                        None,
                    )

        return event

    def get(
        self,
        event_id: str,
    ) -> JarminBridgeEvent:
        with self._lock:
            try:
                return self._events[
                    event_id
                ]

            except KeyError as error:
                raise KeyError(
                    "Jarmin olayı bulunamadı."
                ) from error

    def list(
        self,
        *,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[JarminBridgeEvent]:
        if limit <= 0:
            raise ValueError(
                "Olay sınırı pozitif "
                "olmalıdır."
            )

        with self._lock:
            events = [
                self._events[event_id]
                for event_id
                in self._order
            ]

        if event_type is not None:
            normalized = (
                event_type.strip().lower()
            )

            events = [
                event
                for event in events
                if (
                    event.event_type
                    == normalized
                )
            ]

        return events[-limit:]

    def snapshot(
        self,
    ) -> dict[str, Any]:
        events = self.list(
            limit=self.maximum_events
        )

        return {
            "schema": (
                "sykasif-jarmin-event-bridge/v1"
            ),
            "event_count": len(events),
            "events": [
                event.as_dict()
                for event in events
            ],
            "pending_notifications": (
                self.notifications.pending()
            ),
        }