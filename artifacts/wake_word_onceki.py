from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True, slots=True)
class WakeWordResult:
    detected: bool
    wake_word: str | None
    command_text: str
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "wake_word": self.wake_word,
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
    def __init__(
        self,
        wake_words: tuple[str, ...] = (
            "jarmin",
            "hey jarmin",
            "jarmin dinle",
        ),
    ) -> None:
        self.wake_words = tuple(
            item.strip().lower()
            for item in wake_words
            if item.strip()
        )

        if not self.wake_words:
            raise ValueError(
                "En az bir uyandırma sözcüğü "
                "tanımlanmalıdır."
            )

    def detect(
        self,
        text: str,
    ) -> WakeWordResult:
        normalized = self._normalize(
            text
        )

        if not normalized:
            return WakeWordResult(
                detected=False,
                wake_word=None,
                command_text="",
                confidence=0.0,
            )

        ordered = sorted(
            self.wake_words,
            key=len,
            reverse=True,
        )

        for wake_word in ordered:
            pattern = (
                r"^\s*"
                + re.escape(wake_word)
                + r"[\s,;:!?-]*(.*)$"
            )

            match = re.match(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            command = match.group(1).strip()

            return WakeWordResult(
                detected=True,
                wake_word=wake_word,
                command_text=command,
                confidence=99.0,
            )

        return WakeWordResult(
            detected=False,
            wake_word=None,
            command_text=normalized,
            confidence=20.0,
        )

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        value = str(
            text or ""
        ).strip().lower()

        return re.sub(
            r"\s+",
            " ",
            value,
        )