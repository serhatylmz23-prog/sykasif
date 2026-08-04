from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol


class SpeechRecognitionBackend(
    Protocol
):
    backend_id: str

    def transcribe(
        self,
        audio: bytes,
        *,
        sample_rate: int,
        channels: int,
        language: str,
    ) -> str:
        ...


@dataclass(frozen=True, slots=True)
class TranscriptResult:
    text: str
    language: str
    backend_id: str
    audio_sha256: str
    byte_count: int
    sample_rate: int
    channels: int
    digital_confidence: float
    simulated: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "backend_id": self.backend_id,
            "audio_sha256": (
                self.audio_sha256
            ),
            "byte_count": self.byte_count,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "digital_confidence": round(
                min(
                    99.9,
                    max(
                        0.0,
                        self.digital_confidence,
                    ),
                ),
                3,
            ),
            "simulated": self.simulated,
            "field_validation_required": True,
        }


class TextFixtureRecognitionBackend:
    backend_id = "text_fixture"

    def transcribe(
        self,
        audio: bytes,
        *,
        sample_rate: int,
        channels: int,
        language: str,
    ) -> str:
        try:
            return audio.decode(
                "utf-8"
            ).strip()
        except UnicodeDecodeError as error:
            raise RuntimeError(
                "Test ses verisi UTF-8 metin "
                "olarak çözülemedi."
            ) from error


class SpeechToTextEngine:
    def __init__(
        self,
        backend: (
            SpeechRecognitionBackend
            | None
        ) = None,
    ) -> None:
        self.backend = (
            backend
            or TextFixtureRecognitionBackend()
        )

    def transcribe(
        self,
        audio: bytes,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        language: str = "tr-TR",
    ) -> TranscriptResult:
        self._validate(
            audio=audio,
            sample_rate=sample_rate,
            channels=channels,
        )

        text = self.backend.transcribe(
            audio,
            sample_rate=sample_rate,
            channels=channels,
            language=language,
        ).strip()

        if not text:
            raise ValueError(
                "Ses verisinden metin "
                "üretilemedi."
            )

        simulated = (
            self.backend.backend_id
            == "text_fixture"
        )

        confidence = (
            80.0
            if simulated
            else 90.0
        )

        return TranscriptResult(
            text=text,
            language=language,
            backend_id=(
                self.backend.backend_id
            ),
            audio_sha256=sha256(
                audio
            ).hexdigest(),
            byte_count=len(audio),
            sample_rate=sample_rate,
            channels=channels,
            digital_confidence=confidence,
            simulated=simulated,
        )

    @staticmethod
    def _validate(
        *,
        audio: bytes,
        sample_rate: int,
        channels: int,
    ) -> None:
        if not audio:
            raise ValueError(
                "Ses verisi boş olamaz."
            )

        if sample_rate < 8000:
            raise ValueError(
                "Örnekleme hızı en az "
                "8000 Hz olmalıdır."
            )

        if channels not in {
            1,
            2,
        }:
            raise ValueError(
                "Yalnız tek veya çift kanal "
                "desteklenir."
            )