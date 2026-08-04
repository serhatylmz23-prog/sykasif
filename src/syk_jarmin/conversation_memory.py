from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    message_id: str
    role: str
    content: str
    created_at: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ConversationSession:
    session_id: str
    created_at: str
    updated_at: str
    messages: tuple[
        ConversationMessage,
        ...,
    ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(
                self.messages
            ),
            "messages": [
                message.as_dict()
                for message in self.messages
            ],
        }


class ConversationMemory:
    VALID_ROLES = {
        "user",
        "assistant",
        "system",
        "tool",
    }

    def __init__(
        self,
        *,
        maximum_messages_per_session: int = 200,
    ) -> None:
        if maximum_messages_per_session <= 0:
            raise ValueError(
                "Azami mesaj sayısı pozitif olmalıdır."
            )

        self.maximum_messages_per_session = (
            maximum_messages_per_session
        )

        self._sessions: dict[
            str,
            dict[str, Any],
        ] = {}

        self._lock = RLock()

    def create_session(
        self,
        session_id: str | None = None,
    ) -> ConversationSession:
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
            if resolved_id not in self._sessions:
                self._sessions[
                    resolved_id
                ] = {
                    "created_at": now,
                    "updated_at": now,
                    "messages": [],
                }

        return self.get_session(
            resolved_id
        )

    def append(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        normalized_role = role.strip().lower()
        normalized_content = content.strip()

        if normalized_role not in self.VALID_ROLES:
            raise ValueError(
                f"Geçersiz konuşma rolü: {role}"
            )

        if not normalized_content:
            raise ValueError(
                "Konuşma içeriği boş olamaz."
            )

        with self._lock:
            if session_id not in self._sessions:
                self.create_session(
                    session_id
                )

            now = datetime.now(
                UTC
            ).isoformat()

            message = ConversationMessage(
                message_id=(
                    f"MSG-{uuid4().hex[:24]}"
                ),
                role=normalized_role,
                content=normalized_content,
                created_at=now,
                metadata=dict(
                    metadata or {}
                ),
            )

            messages = self._sessions[
                session_id
            ]["messages"]

            messages.append(message)

            overflow = (
                len(messages)
                - self.maximum_messages_per_session
            )

            if overflow > 0:
                del messages[:overflow]

            self._sessions[
                session_id
            ]["updated_at"] = now

            return message

    def get_session(
        self,
        session_id: str,
    ) -> ConversationSession:
        with self._lock:
            try:
                record = self._sessions[
                    session_id
                ]
            except KeyError as error:
                raise KeyError(
                    f"Jarmin oturumu bulunamadı: "
                    f"{session_id}"
                ) from error

            return ConversationSession(
                session_id=session_id,
                created_at=record[
                    "created_at"
                ],
                updated_at=record[
                    "updated_at"
                ],
                messages=tuple(
                    record["messages"]
                ),
            )

    def recent(
        self,
        session_id: str,
        *,
        limit: int = 20,
    ) -> list[ConversationMessage]:
        if limit <= 0:
            raise ValueError(
                "Mesaj sınırı pozitif olmalıdır."
            )

        session = self.get_session(
            session_id
        )

        return list(
            session.messages[-limit:]
        )

    def clear(
        self,
        session_id: str,
    ) -> ConversationSession:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(session_id)

            now = datetime.now(
                UTC
            ).isoformat()

            self._sessions[
                session_id
            ]["messages"] = []

            self._sessions[
                session_id
            ]["updated_at"] = now

        return self.get_session(
            session_id
        )

    def list_sessions(
        self,
    ) -> list[ConversationSession]:
        with self._lock:
            ids = list(
                self._sessions
            )

        return [
            self.get_session(session_id)
            for session_id in ids
        ]

    def snapshot(
        self,
    ) -> dict[str, Any]:
        sessions = self.list_sessions()

        unsigned = {
            "schema": (
                "sykasif-jarmin-memory/v1"
            ),
            "session_count": len(
                sessions
            ),
            "sessions": [
                session.as_dict()
                for session in sessions
            ],
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