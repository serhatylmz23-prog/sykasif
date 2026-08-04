from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any
from uuid import uuid4


SUPPORTED_EVENT_TYPES = {
    "analysis_completed",
    "evidence_created",
    "report_created",
    "device_disconnected",
    "critical_event",
    "system_information",
}

NOTIFICATION_LEVELS = {
    "information",
    "success",
    "warning",
    "critical",
}


@dataclass(frozen=True, slots=True)
class NotificationRecord:
    notification_id: str
    event_type: str
    title: str
    message: str
    level: str
    sound_profile: str
    encrypted_channel: bool
    acknowledged: bool
    created_at: str
    notification_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "sykasif-jarmin-notification/v1",
            "notification_id": self.notification_id,
            "event_type": self.event_type,
            "title": self.title,
            "message": self.message,
            "level": self.level,
            "sound_profile": self.sound_profile,
            "encrypted_channel": self.encrypted_channel,
            "acknowledged": self.acknowledged,
            "created_at": self.created_at,
            "notification_sha256": self.notification_sha256,
        }


class NotificationRouter:
    EVENT_CONFIGURATION = {
        "analysis_completed": {
            "title": "Analiz Tamamlandı",
            "level": "success",
            "sound_profile": "kasif_analysis",
        },
        "evidence_created": {
            "title": "Dijital Kanıt Hazır",
            "level": "success",
            "sound_profile": "kasif_evidence",
        },
        "report_created": {
            "title": "Mühürlü Rapor Hazır",
            "level": "success",
            "sound_profile": "kasif_report",
        },
        "device_disconnected": {
            "title": "Cihaz Bağlantısı Kesildi",
            "level": "warning",
            "sound_profile": "kasif_warning",
        },
        "critical_event": {
            "title": "Kritik Olay",
            "level": "critical",
            "sound_profile": "kasif_critical",
        },
        "system_information": {
            "title": "SyKaşif Bilgilendirmesi",
            "level": "information",
            "sound_profile": "kasif_information",
        },
    }

    def __init__(
        self,
        *,
        maximum_notifications: int = 500,
    ) -> None:
        if maximum_notifications <= 0:
            raise ValueError(
                "Azami bildirim sayısı pozitif olmalıdır."
            )

        self.maximum_notifications = maximum_notifications
        self._records: dict[str, NotificationRecord] = {}
        self._order: list[str] = []
        self._lock = RLock()

    def route(
        self,
        *,
        event_type: str,
        message: str,
        title: str | None = None,
        encrypted_channel: bool = True,
    ) -> NotificationRecord:
        normalized_type = event_type.strip().lower()
        normalized_message = message.strip()

        if normalized_type not in SUPPORTED_EVENT_TYPES:
            raise ValueError(
                f"Desteklenmeyen bildirim olay türü: {normalized_type}"
            )

        if not normalized_message:
            raise ValueError(
                "Bildirim mesajı boş olamaz."
            )

        configuration = self.EVENT_CONFIGURATION[
            normalized_type
        ]

        resolved_title = (
            title.strip()
            if title and title.strip()
            else configuration["title"]
        )

        level = configuration["level"]

        if level not in NOTIFICATION_LEVELS:
            raise RuntimeError(
                "Bildirim önem seviyesi geçersiz."
            )

        notification_id = (
            f"JNT-{uuid4().hex[:24]}"
        )

        created_at = datetime.now(
            UTC
        ).isoformat()

        unsigned = {
            "notification_id": notification_id,
            "event_type": normalized_type,
            "title": resolved_title,
            "message": normalized_message,
            "level": level,
            "sound_profile": configuration[
                "sound_profile"
            ],
            "encrypted_channel": bool(
                encrypted_channel
            ),
            "acknowledged": False,
            "created_at": created_at,
        }

        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        record = NotificationRecord(
            **unsigned,
            notification_sha256=sha256(
                canonical
            ).hexdigest(),
        )

        with self._lock:
            self._records[
                notification_id
            ] = record

            self._order.append(
                notification_id
            )

            self._trim()

        return record

    def get(
        self,
        notification_id: str,
    ) -> NotificationRecord:
        with self._lock:
            try:
                return self._records[
                    notification_id
                ]

            except KeyError as error:
                raise KeyError(
                    "Jarmin bildirimi bulunamadı."
                ) from error

    def acknowledge(
        self,
        notification_id: str,
    ) -> NotificationRecord:
        with self._lock:
            current = self.get(
                notification_id
            )

            unsigned = {
                "notification_id": current.notification_id,
                "event_type": current.event_type,
                "title": current.title,
                "message": current.message,
                "level": current.level,
                "sound_profile": current.sound_profile,
                "encrypted_channel": current.encrypted_channel,
                "acknowledged": True,
                "created_at": current.created_at,
            }

            canonical = json.dumps(
                unsigned,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            updated = NotificationRecord(
                **unsigned,
                notification_sha256=sha256(
                    canonical
                ).hexdigest(),
            )

            self._records[
                notification_id
            ] = updated

        return updated

    def pending(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError(
                "Bildirim sınırı pozitif olmalıdır."
            )

        with self._lock:
            records = [
                self._records[
                    notification_id
                ]
                for notification_id
                in self._order
                if (
                    notification_id
                    in self._records
                    and not self._records[
                        notification_id
                    ].acknowledged
                )
            ]

        return [
            record.as_dict()
            for record in records[-limit:]
        ]

    def list(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError(
                "Bildirim sınırı pozitif olmalıdır."
            )

        with self._lock:
            records = [
                self._records[
                    notification_id
                ]
                for notification_id
                in self._order[-limit:]
                if notification_id
                in self._records
            ]

        return [
            record.as_dict()
            for record in records
        ]

    def snapshot(self) -> dict[str, Any]:
        records = self.list(
            limit=self.maximum_notifications
        )

        unsigned = {
            "schema": (
                "sykasif-jarmin-notification-router/v1"
            ),
            "notification_count": len(records),
            "pending_count": sum(
                1
                for record in records
                if not record["acknowledged"]
            ),
            "notifications": records,
            "status": "ready",
        }

        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return {
            **unsigned,
            "snapshot_sha256": sha256(
                canonical
            ).hexdigest(),
        }

    def _trim(self) -> None:
        overflow = (
            len(self._order)
            - self.maximum_notifications
        )

        if overflow <= 0:
            return

        expired = self._order[:overflow]

        del self._order[:overflow]

        for notification_id in expired:
            self._records.pop(
                notification_id,
                None,
            )


notification_router = NotificationRouter()