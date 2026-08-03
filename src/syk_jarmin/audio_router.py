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
from .voice_profiles import (
    VoiceProfileRegistry,
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
    interaction_mode: str

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
            "interaction_mode": (
                self.interaction_mode
            ),
            "ready_for_kasif": (
                self.wake_word.detected
                and bool(
                    self.command_text
                )
            ),
            # Eski çalışma sözleşmesi.
            "ready_for_jarmin": (
                self.wake_word.detected
                and bool(
                    self.command_text
                )
            ),
        }


@dataclass(frozen=True, slots=True)
class ResponsePlan:
    text: str
    interaction_mode: str
    profile_id: str
    should_speak: bool
    should_display: bool
    synthesis: SynthesisResult | None

    def as_dict(
        self,
        *,
        include_audio: bool = False,
    ) -> dict[str, Any]:
        return {
            "text": self.text,
            "interaction_mode": (
                self.interaction_mode
            ),
            "profile_id": self.profile_id,
            "should_speak": (
                self.should_speak
            ),
            "should_display": (
                self.should_display
            ),
            "synthesis": (
                self.synthesis.as_dict(
                    include_audio=include_audio
                )
                if self.synthesis is not None
                else None
            ),
        }


class AudioRouter:
    MODES = {
        "normal",
        "low_voice",
        "silent",
        "manual",
    }

    def __init__(
        self,
        *,
        speech_to_text: (
            SpeechToTextEngine | None
        ) = None,
        text_to_speech: (
            TextToSpeechEngine | None
        ) = None,
        wake_word: (
            WakeWordEngine | None
        ) = None,
        profiles: (
            VoiceProfileRegistry | None
        ) = None,
        interaction_mode: str = "normal",
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

        self.profiles = (
            profiles
            or VoiceProfileRegistry()
        )

        self.interaction_mode = (
            self._validate_mode(
                interaction_mode
            )
        )

    def configure(
        self,
        *,
        interaction_mode: str | None = None,
        wake_words: (
            tuple[str, ...] | None
        ) = None,
        legacy_wake_words: (
            bool | None
        ) = None,
        **_: Any,
    ) -> dict[str, Any]:
        if interaction_mode is not None:
            self.interaction_mode = (
                self._validate_mode(
                    interaction_mode
                )
            )

        if (
            wake_words is not None
            or legacy_wake_words is not None
        ):
            self.wake_word.configure(
                wake_words=wake_words,
                legacy_enabled=(
                    legacy_wake_words
                ),
            )

        return self.snapshot()

    def receive(
        self,
        audio: bytes,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        language: str = "tr-TR",
        interaction_mode: str | None = None,
    ) -> AudioCommandResult:
        mode = self._validate_mode(
            interaction_mode
            or self.interaction_mode
        )

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
            interaction_mode=mode,
        )

    def prepare_response(
        self,
        text: str,
        *,
        profile_id: str = (
            "kasif_default"
        ),
        interaction_mode: str | None = None,
    ) -> ResponsePlan:
        normalized = str(
            text or ""
        ).strip()

        if not normalized:
            raise ValueError(
                "Yanıt metni boş olamaz."
            )

        profile = self.profiles.get(
            profile_id
        )

        mode = self._validate_mode(
            interaction_mode
            or profile.response_mode
            or self.interaction_mode
        )

        should_speak = (
            mode == "normal"
        )

        should_display = True

        synthesis = None

        if should_speak:
            synthesis = (
                self.text_to_speech
                .synthesize(
                    normalized,
                    profile_id=profile_id,
                )
            )

        return ResponsePlan(
            text=normalized,
            interaction_mode=mode,
            profile_id=profile.profile_id,
            should_speak=should_speak,
            should_display=should_display,
            synthesis=synthesis,
        )

    def respond(
        self,
        text: str,
        *,
        profile_id: str = (
            "jarmin_default"
        ),
    ) -> SynthesisResult:
        # Eski sözleşme korunur:
        # respond her zaman ses paketi döndürür.
        return (
            self.text_to_speech
            .synthesize(
                text,
                profile_id=profile_id,
            )
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-kasif-audio-router/v1"
            ),
            "assistant_name": "Kaşif",
            "friendly_name": "Babuş",
            "interaction_mode": (
                self.interaction_mode
            ),
            "available_modes": sorted(
                self.MODES
            ),
            "wake_word": (
                self.wake_word.snapshot()
            ),
            "profiles": (
                self.profiles.snapshot()
            ),
            "status": "ready",
        }

    @classmethod
    def _validate_mode(
        cls,
        mode: str,
    ) -> str:
        normalized = str(
            mode or ""
        ).strip().lower()

        if normalized not in cls.MODES:
            raise ValueError(
                "Geçersiz ses etkileşim modu: "
                f"{mode}"
            )

        return normalized