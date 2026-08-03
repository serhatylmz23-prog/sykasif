from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any
from uuid import uuid4


RUNTIME_STATES = {
    "created",
    "ready",
    "running",
    "stopped",
    "error",
}


@dataclass(frozen=True, slots=True)
class JarminRuntimeResult:
    request_id: str
    session_id: str
    command: str
    intent: str
    response: str
    status: str
    source: str
    created_at: str
    result_sha256: str
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "sykasif-kasif-runtime-result/v1",
            "request_id": self.request_id,
            "session_id": self.session_id,
            "command": self.command,
            "intent": self.intent,
            "response": self.response,
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at,
            "result_sha256": self.result_sha256,
            "metadata": dict(self.metadata),
        }



class _KasifVoiceCompatibilityRuntime:
    """Kaşif ses ayarları için uyumluluk katmanı."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {
            "language": "tr-TR",
            "wake_words": [
                "Kaşif",
                "Babuş",
            ],
        }

    def configure(
        self,
        settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        incoming = {
            **dict(settings or {}),
            **kwargs,
        }

        wake_word = incoming.pop(
            "wake_word",
            None,
        )

        wake_words = incoming.pop(
            "wake_words",
            None,
        )

        if wake_words is not None:
            resolved = [
                str(value).strip()
                for value in wake_words
                if str(value).strip()
            ]

            if resolved:
                self.settings[
                    "wake_words"
                ] = resolved

        elif wake_word is not None:
            resolved = str(
                wake_word
            ).strip()

            if resolved:
                current = list(
                    self.settings.get(
                        "wake_words",
                        [],
                    )
                )

                if resolved not in current:
                    current.insert(
                        0,
                        resolved,
                    )

                self.settings[
                    "wake_words"
                ] = current

        self.settings.update(
            incoming
        )

        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        settings = dict(
            self.settings
        )

        return {
            "schema": (
                "sykasif-kasif-voice-compatibility/v1"
            ),
            "assistant_name": "Kaşif",
            **settings,
            "settings": settings,
            "status": "ready",
        }


class JarminRuntime:
    """
    Kaşif konuşan asistan çalışma katmanı.

    Eski Jarmin adlandırmasını import uyumluluğu için korur.
    Kullanıcıya görünen asistan adı Kaşif'tir.
    """

    def __init__(
        self,
        *,
        intent_engine: Any | None = None,
        command_router: Any | None = None,
        device_bridge: Any | None = None,
        voice_runtime: Any | None = None,
        notification_router: Any | None = None,
        conversation_memory: Any | None = None,
        assistant_name: str = "Kaşif",
        maximum_history: int = 500,
        **_: Any,
    ) -> None:
        if maximum_history <= 0:
            raise ValueError(
                "Azami geçmiş sayısı pozitif olmalıdır."
            )

        normalized_name = assistant_name.strip()

        if not normalized_name:
            raise ValueError(
                "Asistan adı boş olamaz."
            )

        self.intent_engine = intent_engine

        if command_router is None:
            from .command_router import (
                CommandRouter,
            )

            command_router = CommandRouter()

        self.command_router = command_router
        self.device_bridge = device_bridge
        if voice_runtime is None:
            voice_runtime = (
                _KasifVoiceCompatibilityRuntime()
            )

        self.voice_runtime = voice_runtime

        if notification_router is None:
            from .notification_router import (
                NotificationRouter,
            )

            notification_router = (
                NotificationRouter()
            )

        self.notification_router = (
            notification_router
        )

        # Eski entegrasyon katmanının beklediği
        # geriye dönük uyumluluk adı.
        self.notifications = (
            notification_router
        )

        self.conversation_memory = (
            conversation_memory
        )

        self.assistant_name = normalized_name

        # Eski entegrasyon katmanının
        # beklediği geriye dönük uyumluluk alanı.
        self.assistant = self

        self.maximum_history = maximum_history

        # BEGIN SYK_JARMIN_INTEGRATION_CONTRACT
        # Entegrasyon katmanı için tam
        # geriye dönük uyumluluk sözleşmesi.
        self.assistant = self
        self.core = self
        self.runtime = self
        self.kasif = self
        self.jarmin = self

        self.notifications = self.notification_router
        self.notification = self.notification_router

        self.voice = self.voice_runtime

        self.commands = self.command_router
        self.command = self.command_router

        self.devices = self.device_bridge
        self.device = self.device_bridge

        self.memory = self.conversation_memory

        self.intent = self.intent_engine
        self.intents = self.intent_engine

        self.name = self.assistant_name
        self.display_name = self.assistant_name
        # END SYK_JARMIN_INTEGRATION_CONTRACT


        self._state = "ready"
        self.status = self._state
        self._history: list[JarminRuntimeResult] = []
        self._lock = RLock()
        self._last_error: str | None = None

    @property
    def state(self) -> str:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state == "running"

    def configure(
        self,
        settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Kaşif çalışma ayarlarını günceller."""

        incoming = {
            **dict(settings or {}),
            **kwargs,
        }

        assistant_name = incoming.pop(
            "assistant_name",
            incoming.pop(
                "display_name",
                incoming.pop(
                    "name",
                    None,
                ),
            ),
        )

        maximum_history = incoming.pop(
            "maximum_history",
            incoming.pop(
                "history_limit",
                None,
            ),
        )

        wake_words = incoming.pop(
            "wake_words",
            None,
        )

        wake_word = incoming.pop(
            "wake_word",
            None,
        )

        if assistant_name is not None:
            resolved_name = str(
                assistant_name
            ).strip()

            if not resolved_name:
                raise ValueError(
                    "Asistan adı boş olamaz."
                )

            self.assistant_name = resolved_name
            self.name = resolved_name
            self.display_name = resolved_name

        if maximum_history is not None:
            resolved_limit = int(
                maximum_history
            )

            if resolved_limit <= 0:
                raise ValueError(
                    "Geçmiş sınırı pozitif olmalıdır."
                )

            self.maximum_history = resolved_limit

        voice_settings = {
            key: incoming.pop(key)
            for key in list(incoming)
            if key in {
                "language",
                "locale",
                "enabled",
                "sample_rate",
                "channels",
                "input_device",
                "output_device",
                "speech_to_text_enabled",
                "text_to_speech_enabled",
                "notification_sound_enabled",
            }
        }

        if wake_words is not None:
            voice_settings["wake_words"] = (
                wake_words
            )

        elif wake_word is not None:
            voice_settings["wake_word"] = (
                wake_word
            )

        else:
            voice_settings["wake_words"] = [
                "Kaşif",
                "Babuş",
            ]

        voice_configure = getattr(
            self.voice_runtime,
            "configure",
            None,
        )

        voice_snapshot = None

        if callable(voice_configure):
            voice_snapshot = voice_configure(
                **voice_settings
            )

        if not hasattr(
            self,
            "_settings",
        ):
            self._settings = {}

        self._settings.update(
            incoming
        )

        return {
            **self.snapshot(),
            "assistant_name": (
                self.assistant_name
            ),
            "wake_words": [
                "Kaşif",
                "Babuş",
            ],
            "voice": voice_snapshot,
            "applied_settings": {
                **incoming,
                **voice_settings,
            },
        }


    def start(self) -> dict[str, Any]:
        with self._lock:
            self._state = "running"
            self._last_error = None

        return self.snapshot()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self._state = "stopped"

        return self.snapshot()

    def execute(
        self,
        command: str | None = None,
        *,
        text: str | None = None,
        session_id: str | None = None,
        source: str = "runtime",
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> JarminRuntimeResult:
        resolved_command = (
            command
            if command is not None
            else text
        )

        normalized_command = str(
            resolved_command or ""
        ).strip()

        if not normalized_command:
            raise ValueError(
                "Kaşif komutu boş olamaz."
            )

        resolved_session_id = (
            session_id.strip()
            if session_id
            else f"KASIF-SES-{uuid4().hex[:20]}"
        )

        resolved_source = (
            source.strip()
            or "runtime"
        )

        resolved_context = {
            **dict(context or {}),
            **dict(metadata or {}),
            **kwargs,
        }

        try:
            intent = self._resolve_intent(
                normalized_command,
                resolved_context,
            )

            routed = self._route_command(
                command=normalized_command,
                intent=intent,
                session_id=resolved_session_id,
                context=resolved_context,
            )

            response = self._resolve_response(
                command=normalized_command,
                intent=intent,
                routed=routed,
            )

            result = self._build_result(
                session_id=resolved_session_id,
                command=normalized_command,
                intent=intent,
                response=response,
                status="completed",
                source=resolved_source,
                metadata={
                    "assistant_name": self.assistant_name,
                    "routed": routed,
                    "digital_scope": True,
                    "field_validation_required": False,
                },
            )

            self._remember(result)

            with self._lock:
                self._state = "running"
                self._last_error = None

            return result

        except Exception as error:
            with self._lock:
                self._state = "error"
                self._last_error = str(error)

            raise

    def process(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> JarminRuntimeResult:
        return self.execute(
            command,
            **kwargs,
        )

    def handle(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> JarminRuntimeResult:
        return self.execute(
            command,
            **kwargs,
        )

    def run(
        self,
        command: str | None = None,
        **kwargs: Any,
    ) -> JarminRuntimeResult:
        return self.execute(
            command,
            **kwargs,
        )

    def ask(
        self,
        text: str,
        **kwargs: Any,
    ) -> JarminRuntimeResult:
        return self.execute(
            text=text,
            **kwargs,
        )

    def history(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError(
                "Geçmiş sınırı pozitif olmalıdır."
            )

        with self._lock:
            records = self._history[-limit:]

        return [
            record.as_dict()
            for record in records
        ]

    def clear_history(self) -> int:
        with self._lock:
            count = len(self._history)
            self._history.clear()

        return count

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            unsigned = {
                "schema": "sykasif-kasif-runtime/v1",
                "assistant_name": self.assistant_name,
                "legacy_runtime_name": "JarminRuntime",
                "state": self._state,
                "history_count": len(self._history),
                "last_error": self._last_error,
                "components": {
                    "intent_engine": (
                        self.intent_engine is not None
                    ),
                    "command_router": (
                        self.command_router is not None
                    ),
                    "device_bridge": (
                        self.device_bridge is not None
                    ),
                    "voice_runtime": (
                        self.voice_runtime is not None
                    ),
                    "notification_router": (
                        self.notification_router is not None
                    ),
                    "conversation_memory": (
                        self.conversation_memory is not None
                    ),
                },
                "status": "ready",
            }

        # BEGIN SYK_KASIF_DURUM_CIKTISI
        assistant_settings = dict(
            getattr(
                self,
                "_settings",
                {},
            )
        )

        voice_snapshot = None

        voice_snapshot_method = getattr(
            self.voice_runtime,
            "snapshot",
            None,
        )

        if callable(
            voice_snapshot_method
        ):
            voice_snapshot = (
                voice_snapshot_method()
            )

        notification_snapshot = None

        notification_snapshot_method = getattr(
            self.notification_router,
            "snapshot",
            None,
        )

        if callable(
            notification_snapshot_method
        ):
            notification_snapshot = (
                notification_snapshot_method()
            )

        unsigned["assistant"] = {
            "name": self.assistant_name,
            "display_name": (
                self.assistant_name
            ),
            "active": bool(
                assistant_settings.get(
                    "active",
                    True,
                )
            ),
            "voice_enabled": bool(
                assistant_settings.get(
                    "voice_enabled",
                    True,
                )
            ),
            "notification_enabled": bool(
                assistant_settings.get(
                    "notification_enabled",
                    True,
                )
            ),
            "wake_words": [
                "Kaşif",
                "Babuş",
            ],
            "status": self._state,
        }

        unsigned["voice"] = (
            voice_snapshot
        )

        unsigned["notifications"] = (
            notification_snapshot
        )
        # END SYK_KASIF_DURUM_CIKTISI
        return {
            **unsigned,
            "snapshot_sha256": self._hash(
                unsigned
            ),
        }

    def _resolve_intent(
        self,
        command: str,
        context: dict[str, Any],
    ) -> str:
        engine = self.intent_engine

        if engine is not None:
            for method_name in (
                "detect",
                "resolve",
                "classify",
                "analyze",
                "parse",
            ):
                method = getattr(
                    engine,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                try:
                    result = method(
                        command,
                        context=context,
                    )
                except TypeError:
                    result = method(command)

                intent = self._extract_intent(
                    result
                )

                if intent:
                    return intent

        lowered = command.casefold()

        rules = (
            (
                (
                    "rapor",
                    "pdf",
                    "mühür",
                ),
                "report",
            ),
            (
                (
                    "kamera",
                    "fotoğraf",
                    "görüntü",
                    "video",
                ),
                "camera",
            ),
            (
                (
                    "mikrofon",
                    "ses",
                    "dinle",
                ),
                "microphone",
            ),
            (
                (
                    "gps",
                    "konum",
                    "koordinat",
                    "harita",
                ),
                "location",
            ),
            (
                (
                    "analiz",
                    "incele",
                    "değerlendir",
                ),
                "analysis",
            ),
            (
                (
                    "bildirim",
                    "uyarı",
                ),
                "notification",
            ),
            (
                (
                    "durum",
                    "sistem",
                    "hazır",
                ),
                "system_status",
            ),
        )

        for keywords, intent in rules:
            if any(
                keyword in lowered
                for keyword in keywords
            ):
                return intent

        return "conversation"

    def _route_command(
        self,
        *,
        command: str,
        intent: str,
        session_id: str,
        context: dict[str, Any],
    ) -> Any:
        router = self.command_router

        if router is None:
            return None

        for method_name in (
            "route",
            "execute",
            "dispatch",
            "handle",
            "process",
        ):
            method = getattr(
                router,
                method_name,
                None,
            )

            if not callable(method):
                continue

            attempts = (
                {
                    "command": command,
                    "intent": intent,
                    "session_id": session_id,
                    "context": context,
                },
                {
                    "text": command,
                    "intent": intent,
                    "context": context,
                },
                {
                    "command": command,
                },
            )

            for arguments in attempts:
                try:
                    return method(
                        **arguments
                    )
                except TypeError:
                    continue

        return None

    def _resolve_response(
        self,
        *,
        command: str,
        intent: str,
        routed: Any,
    ) -> str:
        routed_response = (
            self._extract_response(
                routed
            )
        )

        if routed_response:
            return routed_response

        responses = {
            "report": (
                "Raporlama isteği alındı. "
                "Doğrulanabilir dijital kayıtlar "
                "üzerinden işlem hazırlanıyor."
            ),
            "camera": (
                "Kamera işlemi için cihaz izni ve "
                "görüntü akışı kontrol ediliyor."
            ),
            "microphone": (
                "Mikrofon işlemi için ses çalışma "
                "ortamı kontrol ediliyor."
            ),
            "location": (
                "Konum ve harita çalışma alanı "
                "kontrol ediliyor."
            ),
            "analysis": (
                "Analiz isteği alındı. Sonuçlar "
                "kanıta dayalı dijital kapsamda "
                "değerlendirilecek."
            ),
            "notification": (
                "Bildirim ayarları kontrol ediliyor."
            ),
            "system_status": (
                "Kaşif çalışma ortamı hazır."
            ),
            "conversation": (
                f"Kaşif isteğinizi aldı: {command}"
            ),
        }

        return responses.get(
            intent,
            responses["conversation"],
        )

    def _build_result(
        self,
        *,
        session_id: str,
        command: str,
        intent: str,
        response: str,
        status: str,
        source: str,
        metadata: dict[str, Any],
    ) -> JarminRuntimeResult:
        request_id = (
            f"KASIF-REQ-{uuid4().hex[:24]}"
        )

        created_at = datetime.now(
            UTC
        ).isoformat()

        unsigned = {
            "request_id": request_id,
            "session_id": session_id,
            "command": command,
            "intent": intent,
            "response": response,
            "status": status,
            "source": source,
            "created_at": created_at,
            "metadata": metadata,
        }

        return JarminRuntimeResult(
            **unsigned,
            result_sha256=self._hash(
                unsigned
            ),
        )

    def _remember(
        self,
        result: JarminRuntimeResult,
    ) -> None:
        memory = self.conversation_memory

        if memory is not None:
            for method_name in (
                "add",
                "remember",
                "store",
                "append",
                "save",
            ):
                method = getattr(
                    memory,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                try:
                    method(
                        result.as_dict()
                    )
                    break
                except TypeError:
                    continue

        with self._lock:
            self._history.append(result)

            overflow = (
                len(self._history)
                - self.maximum_history
            )

            if overflow > 0:
                del self._history[:overflow]

    @staticmethod
    def _extract_intent(
        result: Any,
    ) -> str | None:
        if isinstance(result, str):
            return result.strip() or None

        if isinstance(result, dict):
            for key in (
                "intent",
                "intent_name",
                "name",
                "type",
            ):
                value = result.get(key)

                if value:
                    return str(value).strip()

        for attribute in (
            "intent",
            "intent_name",
            "name",
            "type",
        ):
            value = getattr(
                result,
                attribute,
                None,
            )

            if value:
                return str(value).strip()

        return None

    @staticmethod
    def _extract_response(
        result: Any,
    ) -> str | None:
        if isinstance(result, str):
            return result.strip() or None

        if isinstance(result, dict):
            for key in (
                "response",
                "message",
                "text",
                "result",
            ):
                value = result.get(key)

                if isinstance(value, str):
                    return value.strip() or None

        for attribute in (
            "response",
            "message",
            "text",
            "result",
        ):
            value = getattr(
                result,
                attribute,
                None,
            )

            if isinstance(value, str):
                return value.strip() or None

        return None

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


jarmin_runtime = JarminRuntime()
kasif_runtime = jarmin_runtime
