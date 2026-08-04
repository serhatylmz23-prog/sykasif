from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from typing import Any


@dataclass(frozen=True, slots=True)
class JarminSettings:
    language: str
    voice_enabled: bool
    notification_enabled: bool
    wake_word_enabled: bool
    voice_profile_id: str
    theme_mode: str
    device_id: str | None
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "voice_enabled": (
                self.voice_enabled
            ),
            "notification_enabled": (
                self.notification_enabled
            ),
            "wake_word_enabled": (
                self.wake_word_enabled
            ),
            "voice_profile_id": (
                self.voice_profile_id
            ),
            "theme_mode": self.theme_mode,
            "device_id": self.device_id,
            "updated_at": self.updated_at,
        }


class PersistentJarminSettings:
    DEFAULTS = {
        "language": "tr-TR",
        "voice_enabled": True,
        "notification_enabled": True,
        "wake_word_enabled": True,
        "voice_profile_id": (
            "jarmin_default"
        ),
        "theme_mode": "automatic",
        "device_id": None,
    }

    ALLOWED_THEME_MODES = {
        "automatic",
        "gold",
        "silver",
        "dark",
        "tablet",
        "mobile",
    }

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:
        self.path = (
            Path(path)
            if path is not None
            else Path("artifacts")
            / "jarmin"
            / "settings.json"
        )

        self._lock = RLock()

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.path.is_file():
            self._write(
                dict(self.DEFAULTS)
            )

    def get(self) -> JarminSettings:
        with self._lock:
            payload = self._read()

        return self._to_settings(
            payload
        )

    def update(
        self,
        *,
        language: str | None = None,
        voice_enabled: bool | None = None,
        notification_enabled: (
            bool | None
        ) = None,
        wake_word_enabled: (
            bool | None
        ) = None,
        voice_profile_id: (
            str | None
        ) = None,
        theme_mode: str | None = None,
        device_id: str | None = None,
    ) -> JarminSettings:
        with self._lock:
            payload = self._read()

            if language is not None:
                normalized_language = (
                    language.strip()
                )

                if not normalized_language:
                    raise ValueError(
                        "Dil bilgisi boş olamaz."
                    )

                payload["language"] = (
                    normalized_language
                )

            if voice_enabled is not None:
                payload["voice_enabled"] = (
                    bool(voice_enabled)
                )

            if (
                notification_enabled
                is not None
            ):
                payload[
                    "notification_enabled"
                ] = bool(
                    notification_enabled
                )

            if wake_word_enabled is not None:
                payload[
                    "wake_word_enabled"
                ] = bool(
                    wake_word_enabled
                )

            if voice_profile_id is not None:
                normalized_profile = (
                    voice_profile_id.strip()
                )

                if not normalized_profile:
                    raise ValueError(
                        "Ses profili boş olamaz."
                    )

                payload[
                    "voice_profile_id"
                ] = normalized_profile

            if theme_mode is not None:
                normalized_theme = (
                    theme_mode.strip().lower()
                )

                if (
                    normalized_theme
                    not in self
                    .ALLOWED_THEME_MODES
                ):
                    raise ValueError(
                        "Geçersiz tema modu."
                    )

                payload["theme_mode"] = (
                    normalized_theme
                )

            if device_id is not None:
                normalized_device = (
                    device_id.strip()
                )

                payload["device_id"] = (
                    normalized_device or None
                )

            self._write(payload)

        return self.get()

    def reset(self) -> JarminSettings:
        with self._lock:
            self._write(
                dict(self.DEFAULTS)
            )

        return self.get()

    def snapshot(
        self,
    ) -> dict[str, Any]:
        settings = self.get()

        unsigned = {
            "schema": (
                "sykasif-jarmin-settings/v1"
            ),
            "settings": (
                settings.as_dict()
            ),
        }

        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return {
            **unsigned,
            "settings_sha256": sha256(
                canonical
            ).hexdigest(),
        }

    def _read(self) -> dict[str, Any]:
        try:
            payload = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                "Jarmin ayar dosyası "
                "okunamadı."
            ) from error

        merged = dict(self.DEFAULTS)
        merged.update(payload)

        return merged

    def _write(
        self,
        payload: dict[str, Any],
    ) -> None:
        value = dict(self.DEFAULTS)
        value.update(payload)

        value["updated_at"] = (
            datetime.now(
                UTC
            ).isoformat()
        )

        temporary = self.path.with_suffix(
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            self.path
        )

    @staticmethod
    def _to_settings(
        payload: dict[str, Any],
    ) -> JarminSettings:
        return JarminSettings(
            language=str(
                payload["language"]
            ),
            voice_enabled=bool(
                payload["voice_enabled"]
            ),
            notification_enabled=bool(
                payload[
                    "notification_enabled"
                ]
            ),
            wake_word_enabled=bool(
                payload[
                    "wake_word_enabled"
                ]
            ),
            voice_profile_id=str(
                payload[
                    "voice_profile_id"
                ]
            ),
            theme_mode=str(
                payload["theme_mode"]
            ),
            device_id=payload.get(
                "device_id"
            ),
            updated_at=str(
                payload["updated_at"]
            ),
        )