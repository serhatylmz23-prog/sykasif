from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class VoiceProfile:
    profile_id: str
    title: str
    language: str
    rate: float
    pitch: float
    volume: float
    notification_level: float
    response_mode: str = "normal"
    speaking_style: str = "balanced"

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "title": self.title,
            "language": self.language,
            "rate": self.rate,
            "pitch": self.pitch,
            "volume": self.volume,
            "notification_level": (
                self.notification_level
            ),
            "response_mode": (
                self.response_mode
            ),
            "speaking_style": (
                self.speaking_style
            ),
        }


class VoiceProfileRegistry:
    MODES = {
        "normal",
        "low_voice",
        "silent",
        "manual",
    }

    def __init__(self) -> None:
        default_profile = VoiceProfile(
            profile_id="kasif_default",
            title="Kaşif Varsayılan",
            language="tr-TR",
            rate=0.92,
            pitch=0.96,
            volume=0.84,
            notification_level=0.72,
            response_mode="normal",
            speaking_style="balanced",
        )

        field_profile = VoiceProfile(
            profile_id="kasif_field",
            title="Kaşif Saha",
            language="tr-TR",
            rate=0.96,
            pitch=0.97,
            volume=1.0,
            notification_level=0.90,
            response_mode="normal",
            speaking_style="brief",
        )

        quiet_profile = VoiceProfile(
            profile_id="kasif_quiet",
            title="Kaşif Kısık Ses",
            language="tr-TR",
            rate=0.88,
            pitch=0.96,
            volume=0.40,
            notification_level=0.30,
            response_mode="low_voice",
            speaking_style="written_response",
        )

        silent_profile = VoiceProfile(
            profile_id="kasif_silent",
            title="Kaşif Sessiz",
            language="tr-TR",
            rate=0.90,
            pitch=0.96,
            volume=0.0,
            notification_level=0.0,
            response_mode="silent",
            speaking_style="written_response",
        )

        manual_profile = VoiceProfile(
            profile_id="kasif_manual",
            title="Kaşif Manuel",
            language="tr-TR",
            rate=0.90,
            pitch=0.96,
            volume=0.0,
            notification_level=0.0,
            response_mode="manual",
            speaking_style="screen_only",
        )

        self._profiles = {
            profile.profile_id: profile
            for profile in (
                default_profile,
                field_profile,
                quiet_profile,
                silent_profile,
                manual_profile,
            )
        }

        # Eski iç adlarla uyumluluk.
        self._aliases = {
            "jarmin_default": "kasif_default",
            "jarmin_field": "kasif_field",
            "jarmin_quiet": "kasif_quiet",
        }

    def get(
        self,
        profile_id: str,
    ) -> VoiceProfile:
        normalized = str(
            profile_id or ""
        ).strip()

        resolved = self._aliases.get(
            normalized,
            normalized,
        )

        try:
            return self._profiles[
                resolved
            ]
        except KeyError as error:
            raise KeyError(
                "Ses profili bulunamadı: "
                f"{profile_id}"
            ) from error

    def list(
        self,
    ) -> list[dict[str, Any]]:
        return [
            profile.as_dict()
            for profile
            in self._profiles.values()
        ]

    def ids(
        self,
        *,
        include_legacy: bool = True,
    ) -> tuple[str, ...]:
        values = list(
            self._profiles
        )

        if include_legacy:
            values.extend(
                self._aliases
            )

        return tuple(values)

    def resolve_mode(
        self,
        profile_id: str,
    ) -> str:
        return self.get(
            profile_id
        ).response_mode

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-kasif-voice-profiles/v1"
            ),
            "profiles": self.list(),
            "aliases": dict(
                self._aliases
            ),
            "modes": sorted(
                self.MODES
            ),
            "status": "ready",
        }