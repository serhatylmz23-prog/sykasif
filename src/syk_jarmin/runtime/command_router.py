from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Callable


CommandHandler = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class CommandResult:
    command_id: str
    success: bool
    requires_confirmation: bool
    message: str
    payload: dict[str, Any] = field(
        default_factory=dict
    )
    error: str | None = None
    created_at: str = ""
    result_sha256: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-kasif-command-result/v1"
            ),
            "command_id": self.command_id,
            "success": self.success,
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "message": self.message,
            "payload": dict(self.payload),
            "error": self.error,
            "created_at": self.created_at,
            "result_sha256": (
                self.result_sha256
            ),
        }


# Yeni ve eski adların ikisi de aynı sonucu gösterir.
CommandRouteResult = CommandResult


class CommandRouter:
    DEFAULT_MESSAGES = {
        "open_module": (
            "İstenen bölüm açıldı."
        ),
        "close_module": (
            "İstenen bölüm kapatıldı."
        ),
        "create_report": (
            "Mühürlü rapor hazırlığı başlatıldı."
        ),
        "system_status": (
            "Sistem durumu hazırlandı."
        ),
        "start_analysis": (
            "Analiz işlemi başlatıldı."
        ),
        "stop_analysis": (
            "Analiz işlemi durduruldu."
        ),
        "notification": (
            "Bildirim işlemi tamamlandı."
        ),
        "camera": (
            "Kamera işlemi hazırlandı."
        ),
        "microphone": (
            "Mikrofon işlemi hazırlandı."
        ),
        "location": (
            "Konum işlemi hazırlandı."
        ),
    }

    def __init__(self) -> None:
        self._handlers: dict[
            str,
            CommandHandler,
        ] = {}

        self._lock = RLock()

    def register(
        self,
        command_name: str | None = None,
        handler: CommandHandler | None = None,
        *,
        name: str | None = None,
        command: str | None = None,
        intent: str | None = None,
        replace: bool = True,
        **_: Any,
    ) -> CommandHandler:
        resolved_name = (
            command_name
            or name
            or command
            or intent
        )

        normalized = self._normalize_name(
            resolved_name
        )

        if handler is None:
            def decorator(
                function: CommandHandler,
            ) -> CommandHandler:
                self.register(
                    normalized,
                    function,
                    replace=replace,
                )

                return function

            return decorator

        if not callable(handler):
            raise TypeError(
                "Komut işleyicisi çağrılabilir olmalıdır."
            )

        with self._lock:
            if (
                not replace
                and normalized in self._handlers
            ):
                raise ValueError(
                    f"Komut zaten kayıtlı: {normalized}"
                )

            self._handlers[
                normalized
            ] = handler

        return handler

    def unregister(
        self,
        command_name: str,
    ) -> bool:
        normalized = self._normalize_name(
            command_name
        )

        with self._lock:
            return (
                self._handlers.pop(
                    normalized,
                    None,
                )
                is not None
            )

    def has(
        self,
        command_name: str,
    ) -> bool:
        normalized = self._normalize_name(
            command_name
        )

        with self._lock:
            return normalized in self._handlers

    def execute(
        self,
        command: str | None = None,
        *,
        intent: str | None = None,
        command_name: str | None = None,
        entities: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        confirmed: bool = False,
        requires_confirmation: bool = False,
        **kwargs: Any,
    ) -> CommandResult:
        resolved_name = (
            command_name
            or intent
            or command
        )

        normalized = self._normalize_name(
            resolved_name
        )

        resolved_entities = dict(
            entities or {}
        )

        resolved_context = {
            **dict(context or {}),
            **kwargs,
        }

        if (
            requires_confirmation
            and not confirmed
        ):
            return self._result(
                command_id=normalized,
                success=False,
                requires_confirmation=True,
                message=(
                    "İşlemin devam etmesi için "
                    "onay gerekiyor."
                ),
                payload=resolved_entities,
            )

        with self._lock:
            handler = self._handlers.get(
                normalized
            )

        if handler is None:
            return self._default_result(
                command_id=normalized,
                entities=resolved_entities,
            )

        try:
            handled = self._call_handler(
                handler=handler,
                command_id=normalized,
                entities=resolved_entities,
                context=resolved_context,
                confirmed=confirmed,
            )

            return self._coerce_result(
                command_id=normalized,
                handled=handled,
                entities=resolved_entities,
            )

        except Exception as error:
            return self._result(
                command_id=normalized,
                success=False,
                requires_confirmation=False,
                message=(
                    "Komut işlenirken hata oluştu."
                ),
                payload=resolved_entities,
                error=str(error),
            )

    def route(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> CommandResult:
        return self.execute(
            command,
            **kwargs,
        )

    def dispatch(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> CommandResult:
        return self.execute(
            command,
            **kwargs,
        )

    def handle(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> CommandResult:
        return self.execute(
            command,
            **kwargs,
        )

    def list_commands(self) -> list[str]:
        with self._lock:
            return sorted(
                self._handlers
            )

    def snapshot(self) -> dict[str, Any]:
        commands = self.list_commands()

        unsigned = {
            "schema": (
                "sykasif-kasif-command-router/v1"
            ),
            "command_count": len(commands),
            "commands": commands,
            "default_command_count": len(
                self.DEFAULT_MESSAGES
            ),
            "status": "ready",
        }

        return {
            **unsigned,
            "snapshot_sha256": self._hash(
                unsigned
            ),
        }

    def _default_result(
        self,
        *,
        command_id: str,
        entities: dict[str, Any],
    ) -> CommandResult:
        message = self.DEFAULT_MESSAGES.get(
            command_id
        )

        if message is None:
            return self._result(
                command_id=command_id,
                success=False,
                requires_confirmation=False,
                message=(
                    "Bu komut için kayıtlı bir işlem "
                    "bulunamadı."
                ),
                payload=entities,
            )

        return self._result(
            command_id=command_id,
            success=True,
            requires_confirmation=False,
            message=message,
            payload=entities,
        )

    def _coerce_result(
        self,
        *,
        command_id: str,
        handled: Any,
        entities: dict[str, Any],
    ) -> CommandResult:
        if isinstance(
            handled,
            CommandResult,
        ):
            return handled

        if isinstance(handled, dict):
            payload = handled.get(
                "payload",
                entities,
            )

            return self._result(
                command_id=str(
                    handled.get(
                        "command_id",
                        command_id,
                    )
                ),
                success=bool(
                    handled.get(
                        "success",
                        True,
                    )
                ),
                requires_confirmation=bool(
                    handled.get(
                        "requires_confirmation",
                        False,
                    )
                ),
                message=str(
                    handled.get(
                        "message",
                        self.DEFAULT_MESSAGES.get(
                            command_id,
                            "Komut tamamlandı.",
                        ),
                    )
                ),
                payload=dict(
                    payload or {}
                ),
                error=handled.get(
                    "error"
                ),
            )

        if isinstance(handled, bool):
            return self._result(
                command_id=command_id,
                success=handled,
                requires_confirmation=False,
                message=(
                    "Komut tamamlandı."
                    if handled
                    else "Komut tamamlanamadı."
                ),
                payload=entities,
            )

        if isinstance(handled, str):
            return self._result(
                command_id=command_id,
                success=True,
                requires_confirmation=False,
                message=handled,
                payload=entities,
            )

        if handled is None:
            return self._default_result(
                command_id=command_id,
                entities=entities,
            )

        return self._result(
            command_id=command_id,
            success=True,
            requires_confirmation=False,
            message="Komut tamamlandı.",
            payload={
                **entities,
                "result": handled,
            },
        )

    @staticmethod
    def _call_handler(
        *,
        handler: CommandHandler,
        command_id: str,
        entities: dict[str, Any],
        context: dict[str, Any],
        confirmed: bool,
    ) -> Any:
        attempts = (
            {
                "command_id": command_id,
                "entities": entities,
                "context": context,
                "confirmed": confirmed,
            },
            {
                "command": command_id,
                "entities": entities,
                "context": context,
                "confirmed": confirmed,
            },
            {
                "entities": entities,
                "confirmed": confirmed,
            },
            {},
        )

        last_error: TypeError | None = None

        for arguments in attempts:
            try:
                return handler(
                    **arguments
                )
            except TypeError as error:
                last_error = error

        if last_error is not None:
            raise last_error

        return handler()

    @classmethod
    def _result(
        cls,
        *,
        command_id: str,
        success: bool,
        requires_confirmation: bool,
        message: str,
        payload: dict[str, Any],
        error: str | None = None,
    ) -> CommandResult:
        created_at = datetime.now(
            UTC
        ).isoformat()

        unsigned = {
            "command_id": command_id,
            "success": bool(success),
            "requires_confirmation": bool(
                requires_confirmation
            ),
            "message": str(message),
            "payload": dict(payload),
            "error": error,
            "created_at": created_at,
        }

        return CommandResult(
            **unsigned,
            result_sha256=cls._hash(
                unsigned
            ),
        )

    @staticmethod
    def _normalize_name(
        value: str | None,
    ) -> str:
        normalized = str(
            value or ""
        ).strip().lower()

        if not normalized:
            raise ValueError(
                "Komut adı boş olamaz."
            )

        return normalized

    @staticmethod
    def _hash(
        payload: dict[str, Any],
    ) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

        return sha256(
            canonical
        ).hexdigest()


command_router = CommandRouter()