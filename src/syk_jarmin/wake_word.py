from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class WakeWordResult:
    detected: bool
    wake_word: str | None
    command_text: str
    confidence: float
    matched_alias: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "wake_word": self.wake_word,
            "matched_alias": self.matched_alias,
            "command_text": self.command_text,
            "confidence": round(
                min(
                    99.9,
                    max(
                        0.0,
                        self.confidence,
                    ),
                ),
                3,
            ),
        }


class WakeWordEngine:
    DEFAULT_WAKE_WORDS = (
        "hey kaşif",
        "kaşif dinle",
        "kaşif",
        "hey babuş",
        "babuş dinle",
        "babuş",
    )

    LEGACY_WAKE_WORDS = (
        "hey jarmin",
        "jarmin dinle",
        "jarmin",
    )

    def __init__(
        self,
        wake_words: Iterable[str] | None = None,
        *,
        legacy_enabled: bool = True,
    ) -> None:
        selected = tuple(
            wake_words
            or self.DEFAULT_WAKE_WORDS
        )

        if legacy_enabled:
            selected = (
                *selected,
                *self.LEGACY_WAKE_WORDS,
            )

        normalized: list[str] = []

        for value in selected:
            item = self._normalize(
                value
            )

            if (
                item
                and item not in normalized
            ):
                normalized.append(
                    item
                )

        if not normalized:
            raise ValueError(
                "En az bir uyandırma sözcüğü "
                "tanımlanmalıdır."
            )

        self.wake_words = tuple(
            normalized
        )

        self.legacy_enabled = bool(
            legacy_enabled
        )

    def detect(
        self,
        text: str,
    ) -> WakeWordResult:
        normalized_text = self._normalize(
            text
        )

        if not normalized_text:
            return WakeWordResult(
                detected=False,
                wake_word=None,
                matched_alias=None,
                command_text="",
                confidence=0.0,
            )

        ordered = sorted(
            self.wake_words,
            key=len,
            reverse=True,
        )

        for alias in ordered:
            pattern = (
                r"^\s*"
                + re.escape(alias)
                + r"[\s,;:!?….-]*(.*)$"
            )

            match = re.match(
                pattern,
                normalized_text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            command_text = (
                match.group(1).strip()
            )

            official_name = (
                "Kaşif"
                if "kaşif" in alias
                else (
                    "Babuş"
                    if "babuş" in alias
                    else "Kaşif"
                )
            )

            confidence = (
                99.0
                if alias not in self.LEGACY_WAKE_WORDS
                else 95.0
            )

            return WakeWordResult(
                detected=True,
                wake_word=official_name,
                matched_alias=alias,
                command_text=command_text,
                confidence=confidence,
            )

        return WakeWordResult(
            detected=False,
            wake_word=None,
            matched_alias=None,
            command_text=normalized_text,
            confidence=20.0,
        )

    def configure(
        self,
        *,
        wake_words: Iterable[str] | None = None,
        legacy_enabled: bool | None = None,
    ) -> dict[str, Any]:
        selected_legacy = (
            self.legacy_enabled
            if legacy_enabled is None
            else bool(legacy_enabled)
        )

        replacement = WakeWordEngine(
            wake_words=(
                wake_words
                if wake_words is not None
                else self.wake_words
            ),
            legacy_enabled=selected_legacy,
        )

        self.wake_words = (
            replacement.wake_words
        )

        self.legacy_enabled = (
            replacement.legacy_enabled
        )

        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-kasif-wake-word/v1"
            ),
            "assistant_name": "Kaşif",
            "friendly_name": "Babuş",
            "wake_words": list(
                self.wake_words
            ),
            "legacy_enabled": (
                self.legacy_enabled
            ),
            "status": "ready",
        }

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        value = unicodedata.normalize(
            "NFC",
            str(text or ""),
        )

        value = value.strip().casefold()

        return re.sub(
            r"\s+",
            " ",
            value,
        )