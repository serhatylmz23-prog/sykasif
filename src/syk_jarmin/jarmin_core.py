from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any

from .conversation_memory import (
    ConversationMemory,
)
from .runtime.command_router import (
    CommandResult,
    CommandRouter,
)
from .runtime.intent_engine import (
    IntentEngine,
    IntentResult,
)
from .runtime.session import (
    JarminSessionManager,
)


@dataclass(frozen=True, slots=True)
class JarminResponse:
    session_id: str
    input_text: str
    reply_text: str
    intent: IntentResult
    command: CommandResult
    created_at: str
    response_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-jarmin-response/v1"
            ),
            "session_id": self.session_id,
            "input_text": self.input_text,
            "reply_text": self.reply_text,
            "intent": self.intent.as_dict(),
            "command": self.command.as_dict(),
            "created_at": self.created_at,
            "response_sha256": (
                self.response_sha256
            ),
            "analysis_scope": (
                "digital_assistant_routing"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


class JarminCore:
    def __init__(
        self,
        *,
        memory: ConversationMemory | None = None,
        sessions: JarminSessionManager | None = None,
        intents: IntentEngine | None = None,
        commands: CommandRouter | None = None,
    ) -> None:
        self.memory = (
            memory or ConversationMemory()
        )

        self.sessions = (
            sessions or JarminSessionManager()
        )

        self.intents = (
            intents or IntentEngine()
        )

        self.commands = (
            commands or CommandRouter()
        )

        self._lock = RLock()

    def create_session(
        self,
        *,
        session_id: str | None = None,
        language: str = "tr-TR",
        device_id: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            state = self.sessions.create(
                session_id=session_id,
                language=language,
                device_id=device_id,
            )

            self.memory.create_session(
                state.session_id
            )

        return state.as_dict()

    def process(
        self,
        *,
        session_id: str,
        text: str,
        confirmed: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> JarminResponse:
        normalized_text = str(
            text or ""
        ).strip()

        if not normalized_text:
            raise ValueError(
                "Jarmin komutu boş olamaz."
            )

        session = self.sessions.get(
            session_id
        )

        if session.status != "active":
            raise ValueError(
                "Jarmin oturumu aktif değil."
            )

        self.memory.append(
            session_id=session_id,
            role="user",
            content=normalized_text,
            metadata=metadata,
        )

        intent = self.intents.resolve(
            normalized_text
        )

        command = self.commands.execute(
            intent.intent_id,
            entities=intent.entities,
            confirmed=confirmed,
            requires_confirmation=(
                intent.requires_confirmation
            ),
        )

        reply_text = self._reply(
            intent=intent,
            command=command,
        )

        self.memory.append(
            session_id=session_id,
            role="assistant",
            content=reply_text,
            metadata={
                "intent_id": (
                    intent.intent_id
                ),
                "command_success": (
                    command.success
                ),
            },
        )

        self.sessions.record_turn(
            session_id,
            intent=intent.intent_id,
        )

        created_at = datetime.now(
            UTC
        ).isoformat()

        unsigned = {
            "session_id": session_id,
            "input_text": normalized_text,
            "reply_text": reply_text,
            "intent": intent.as_dict(),
            "command": command.as_dict(),
            "created_at": created_at,
        }

        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return JarminResponse(
            session_id=session_id,
            input_text=normalized_text,
            reply_text=reply_text,
            intent=intent,
            command=command,
            created_at=created_at,
            response_sha256=sha256(
                canonical
            ).hexdigest(),
        )

    def session_snapshot(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        return {
            "session": (
                self.sessions.get(
                    session_id
                ).as_dict()
            ),
            "conversation": (
                self.memory.get_session(
                    session_id
                ).as_dict()
            ),
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-jarmin-core/v1"
            ),
            "sessions": [
                item.as_dict()
                for item in self.sessions.list()
            ],
            "memory": (
                self.memory.snapshot()
            ),
            "commands": list(
                self.commands.available()
            ),
            "language": "tr-TR",
            "status": "ready",
        }

    @staticmethod
    def _reply(
        *,
        intent: IntentResult,
        command: CommandResult,
    ) -> str:
        if command.requires_confirmation:
            return (
                f"{intent.user_message} "
                "Devam etmek için onay gerekiyor."
            )

        if command.success:
            return command.message

        if intent.intent_id in {
            "unknown",
            "empty",
        }:
            return intent.user_message

        return (
            f"{intent.user_message} "
            f"{command.message}"
        )


jarmin_core = JarminCore()