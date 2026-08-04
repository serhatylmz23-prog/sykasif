from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class JarminSessionState:
    session_id: str
    status: str
    language: str
    device_id: str | None
    created_at: str
    updated_at: str
    turn_count: int
    active_intent: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "language": self.language,
            "device_id": self.device_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "turn_count": self.turn_count,
            "active_intent": (
                self.active_intent
            ),
        }


class JarminSessionManager:
    VALID_STATUSES = {
        "active",
        "paused",
        "closed",
    }

    def __init__(self) -> None:
        self._sessions: dict[
            str,
            dict[str, Any],
        ] = {}

        self._lock = RLock()

    def create(
        self,
        *,
        session_id: str | None = None,
        language: str = "tr-TR",
        device_id: str | None = None,
    ) -> JarminSessionState:
        resolved_id = (
            session_id.strip()
            if session_id
            else f"JARMIN-{uuid4().hex[:24]}"
        )

        if not resolved_id:
            raise ValueError(
                "Oturum kimliği boş olamaz."
            )

        now = datetime.now(
            UTC
        ).isoformat()

        with self._lock:
            if resolved_id in self._sessions:
                raise ValueError(
                    "Aynı Jarmin oturumu zaten var."
                )

            self._sessions[
                resolved_id
            ] = {
                "status": "active",
                "language": language,
                "device_id": device_id,
                "created_at": now,
                "updated_at": now,
                "turn_count": 0,
                "active_intent": None,
            }

        return self.get(
            resolved_id
        )

    def get(
        self,
        session_id: str,
    ) -> JarminSessionState:
        with self._lock:
            try:
                value = self._sessions[
                    session_id
                ]
            except KeyError as error:
                raise KeyError(
                    f"Jarmin oturumu bulunamadı: "
                    f"{session_id}"
                ) from error

            return JarminSessionState(
                session_id=session_id,
                status=value["status"],
                language=value["language"],
                device_id=value["device_id"],
                created_at=value["created_at"],
                updated_at=value["updated_at"],
                turn_count=value["turn_count"],
                active_intent=value[
                    "active_intent"
                ],
            )

    def record_turn(
        self,
        session_id: str,
        *,
        intent: str | None,
    ) -> JarminSessionState:
        with self._lock:
            state = self._require(
                session_id
            )

            if state["status"] != "active":
                raise ValueError(
                    "Kapalı veya duraklatılmış "
                    "oturuma yeni tur eklenemez."
                )

            state["turn_count"] += 1
            state["active_intent"] = intent
            state["updated_at"] = (
                datetime.now(
                    UTC
                ).isoformat()
            )

        return self.get(
            session_id
        )

    def set_status(
        self,
        session_id: str,
        status: str,
    ) -> JarminSessionState:
        normalized = status.strip().lower()

        if normalized not in self.VALID_STATUSES:
            raise ValueError(
                f"Geçersiz oturum durumu: "
                f"{status}"
            )

        with self._lock:
            state = self._require(
                session_id
            )

            state["status"] = normalized
            state["updated_at"] = (
                datetime.now(
                    UTC
                ).isoformat()
            )

        return self.get(
            session_id
        )

    def list(
        self,
    ) -> list[JarminSessionState]:
        with self._lock:
            ids = list(
                self._sessions
            )

        return [
            self.get(session_id)
            for session_id in ids
        ]

    def _require(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        try:
            return self._sessions[
                session_id
            ]
        except KeyError as error:
            raise KeyError(
                f"Jarmin oturumu bulunamadı: "
                f"{session_id}"
            ) from error