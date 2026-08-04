from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Callable


CommandHandler = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class CommandRouteResult:
    command_name: str
    handled: bool
    result: Any
    result_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "command_name": self.command_name,
            "handled": self.handled,
            "result": self.result,
            "result_sha256": self.result_sha256,
        }


# Eski çekirdek katmanının kullandığı ad.
# Yeni gerçek sınıf CommandRouteResult'tır.
CommandResult = CommandRouteResult


class CommandRouter:
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

        normalized = str(
            resolved_name or ""
        ).strip().lower()

        if not normalized:
            raise ValueError(
                "Komut adı boş olamaz."
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
        normalized = command_name \
            .strip() \
            .lower()

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
        normalized = command_name \
            .strip() \
            .lower()

        with self._lock:
            return (
                normalized
                in self._handlers
            )

    def route(
        self,
        command: str | None = None,
        *,
        intent: str | None = None,
        command_name: str | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        resolved_name = (
            command_name
            or intent
            or command
        )

        normalized = str(
            resolved_name or ""
        ).strip().lower()

        if not normalized:
            raise ValueError(
                "Yönlendirilecek komut boş olamaz."
            )

        with self._lock:
            handler = self._handlers.get(
                normalized
            )

        if handler is None:
            return None

        call_context = dict(
            context or {}
        )

        try:
            return handler(
                command=command,
                intent=intent,
                context=call_context,
                **kwargs,
            )

        except TypeError:
            try:
                return handler(
                    command,
                    call_context,
                )

            except TypeError:
                return handler()

    def execute(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> Any:
        return self.route(
            command,
            **kwargs,
        )

    def dispatch(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> Any:
        return self.route(
            command,
            **kwargs,
        )

    def handle(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> Any:
        return self.route(
            command,
            **kwargs,
        )

    def list_commands(
        self,
    ) -> list[str]:
        with self._lock:
            return sorted(
                self._handlers
            )

    def snapshot(
        self,
    ) -> dict[str, Any]:
        commands = self.list_commands()

        unsigned = {
            "schema": (
                "sykasif-command-router/v1"
            ),
            "command_count": len(commands),
            "commands": commands,
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


command_router = CommandRouter()