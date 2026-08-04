from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Notification:
    notification_id: str
    level: str
    title: str
    message: str
    sound_id: str
    encrypted_hint: bool
    acknowledged: bool
    created_at: str
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "notification_id": (
                self.notification_id
            ),
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "sound_id": self.sound_id,
            "encrypted_hint": (
                self.encrypted_hint
            ),
            "acknowledged": (
                self.acknowledged
            ),
            "created_at": (
                self.created_at
            ),
            "sha256": self.sha256,
        }


class NotificationEngine:
    LEVELS = {
        "information",
        "success",
        "warning",
        "critical",
    }

    DEFAULT_SOUNDS = {
        "information": "jarmin_info",
        "success": "jarmin_success",
        "warning": "jarmin_warning",
        "critical": "jarmin_secure_alert",
    }

    def __init__(self) -> None:
        self._notifications: dict[
            str,
            Notification,
        ] = {}

        self._order: list[str] = []
        self._lock = RLock()

    def create(
        self,
        *,
        level: str,
        title: str,
        message: str,
        sound_id: str | None = None,
        encrypted_hint: bool = False,
    ) -> Notification:
        normalized_level = (
            level.strip().lower()
        )

        if normalized_level not in self.LEVELS:
            raise ValueError(
                "Geçersiz bildirim seviyesi."
            )

        normalized_title = title.strip()
        normalized_message = message.strip()

        if not normalized_title:
            raise ValueError(
                "Bildirim başlığı boş olamaz."
            )

        if not normalized_message:
            raise ValueError(
                "Bildirim mesajı boş olamaz."
            )

        notification_id = (
            f"NTF-{uuid4().hex[:24]}"
        )

        created_at = datetime.now(
            UTC
        ).isoformat()

        resolved_sound = (
            sound_id
            or self.DEFAULT_SOUNDS[
                normalized_level
            ]
        )

        unsigned = {
            "notification_id": (
                notification_id
            ),
            "level": normalized_level,
            "title": normalized_title,
            "message": normalized_message,
            "sound_id": resolved_sound,
            "encrypted_hint": bool(
                encrypted_hint
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

        notification = Notification(
            **unsigned,
            sha256=sha256(
                canonical
            ).hexdigest(),
        )

        with self._lock:
            self._notifications[
                notification_id
            ] = notification

            self._order.append(
                notification_id
            )

        return notification

    def acknowledge(
        self,
        notification_id: str,
    ) -> Notification:
        with self._lock:
            current = self._require(
                notification_id
            )

            updated = Notification(
                notification_id=(
                    current.notification_id
                ),
                level=current.level,
                title=current.title,
                message=current.message,
                sound_id=current.sound_id,
                encrypted_hint=(
                    current.encrypted_hint
                ),
                acknowledged=True,
                created_at=current.created_at,
                sha256=current.sha256,
            )

            self._notifications[
                notification_id
            ] = updated

            return updated

    def get(
        self,
        notification_id: str,
    ) -> Notification:
        with self._lock:
            return self._require(
                notification_id
            )

    def list(
        self,
        *,
        acknowledged: bool | None = None,
        limit: int = 50,
    ) -> list[Notification]:
        if limit <= 0:
            raise ValueError(
                "Bildirim sınırı pozitif "
                "olmalıdır."
            )

        with self._lock:
            values = [
                self._notifications[
                    notification_id
                ]
                for notification_id
                in self._order
            ]

        if acknowledged is not None:
            values = [
                item
                for item in values
                if (
                    item.acknowledged
                    is acknowledged
                )
            ]

        return values[-limit:]

    def _require(
        self,
        notification_id: str,
    ) -> Notification:
        try:
            return self._notifications[
                notification_id
            ]
        except KeyError as error:
            raise KeyError(
                "Bildirim bulunamadı."
            ) from error