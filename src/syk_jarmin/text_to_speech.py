from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Protocol

from .voice_profiles import (
    VoiceProfile,
    VoiceProfileRegistry,
)


class SpeechSynthesisBackend(
    Protocol
):
    backend_id: str

    def synthesize(
        self,
        text: str,
        *,
        profile: VoiceProfile,
    ) -> bytes:
        ...


class DeterministicSpeechBackend:
    backend_id = "deterministic_preview"

    def synthesize(
        self,
        text: str,
        *,
        profile: VoiceProfile,
    ) -> bytes:
        payload = {
            "schema": (
                "sykasif-jarmin-speech-preview/v1"
            ),
            "text": text,
            "profile": profile.as_dict(),
        }

        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SynthesisResult:
    text: str
    profile_id: str
    backend_id: str
    audio: bytes
    audio_sha256: str
    digital_confidence: float
    preview_only: bool

    def as_dict(
        self,
        *,
        include_audio: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "text": self.text,
            "profile_id": self.profile_id,
            "backend_id": self.backend_id,
            "audio_sha256": (
                self.audio_sha256
            ),
            "byte_count": len(
                self.audio
            ),
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
            "preview_only": (
                self.preview_only
            ),
        }

        if include_audio:
            payload["audio"] = (
                self.audio
            )

        return payload


class TextToSpeechEngine:
    def __init__(
        self,
        backend: (
            SpeechSynthesisBackend
            | None
        ) = None,
        profiles: (
            VoiceProfileRegistry
            | None
        ) = None,
    ) -> None:
        self.backend = (
            backend
            or DeterministicSpeechBackend()
        )

        self.profiles = (
            profiles
            or VoiceProfileRegistry()
        )

    def synthesize(
        self,
        text: str,
        *,
        profile_id: str = (
            "jarmin_default"
        ),
    ) -> SynthesisResult:
        normalized = str(
            text or ""
        ).strip()

        if not normalized:
            raise ValueError(
                "Seslendirilecek metin boş "
                "olamaz."
            )

        if len(normalized) > 5000:
            raise ValueError(
                "Seslendirilecek metin "
                "5000 karakteri aşamaz."
            )

        profile = self.profiles.get(
            profile_id
        )

        audio = self.backend.synthesize(
            normalized,
            profile=profile,
        )

        if not audio:
            raise RuntimeError(
                "Ses üretim motoru boş veri "
                "döndürdü."
            )

        preview_only = (
            self.backend.backend_id
            == "deterministic_preview"
        )

        return SynthesisResult(
            text=normalized,
            # Çağrıda kullanılan profil adını koru.
            # Eski jarmin_* adları içeride kasif_*
            # profillerine yönlendirilse de dış sözleşme
            # çağrılan adı döndürmeye devam eder.
            profile_id=str(profile_id),
            backend_id=(
                self.backend.backend_id
            ),
            audio=audio,
            audio_sha256=sha256(
                audio
            ).hexdigest(),
            digital_confidence=(
                80.0
                if preview_only
                else 90.0
            ),
            preview_only=preview_only,
        )