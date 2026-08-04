from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .speech_to_text import (
    SpeechToTextEngine,
    TranscriptResult,
)
from .text_to_speech import (
    SynthesisResult,
    TextToSpeechEngine,
)
from .wake_word import (
    WakeWordEngine,
    WakeWordResult,
)


@dataclass(frozen=True, slots=True)
class AudioCommandResult:
    transcript: TranscriptResult
    wake_word: WakeWordResult
    command_text: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "transcript": (
                self.transcript.as_dict()
            ),
            "wake_word": (
                self.wake_word.as_dict()
            ),
            "command_text": (
                self.command_text
            ),
            "ready_for_jarmin": (
                self.wake_word.detected
                and bool(
                    self.command_text
                )
            ),
        }


class AudioRouter:
    def __init__(
        self,
        *,
        speech_to_text: (
            SpeechToTextEngine
            | None
        ) = None,
        text_to_speech: (
            TextToSpeechEngine
            | None
        ) = None,
        wake_word: (
            WakeWordEngine
            | None
        ) = None,
    ) -> None:
        self.speech_to_text = (
            speech_to_text
            or SpeechToTextEngine()
        )

        self.text_to_speech = (
            text_to_speech
            or TextToSpeechEngine()
        )

        self.wake_word = (
            wake_word
            or WakeWordEngine()
        )

    def receive(
        self,
        audio: bytes,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        language: str = "tr-TR",
    ) -> AudioCommandResult:
        transcript = (
            self.speech_to_text.transcribe(
                audio,
                sample_rate=sample_rate,
                channels=channels,
                language=language,
            )
        )

        wake_result = (
            self.wake_word.detect(
                transcript.text
            )
        )

        return AudioCommandResult(
            transcript=transcript,
            wake_word=wake_result,
            command_text=(
                wake_result.command_text
            ),
        )

    def respond(
        self,
        text: str,
        *,
        profile_id: str = (
            "jarmin_default"
        ),
    ) -> SynthesisResult:
        return (
            self.text_to_speech
            .synthesize(
                text,
                profile_id=profile_id,
            )
        )