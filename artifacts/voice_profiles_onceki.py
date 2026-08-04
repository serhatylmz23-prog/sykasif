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
        }


class VoiceProfileRegistry:
    def __init__(self) -> None:
        self._profiles = {
            "jarmin_default": VoiceProfile(
                profile_id="jarmin_default",
                title="Jarmin Varsayılan",
                language="tr-TR",
                rate=1.0,
                pitch=1.0,
                volume=0.85,
                notification_level=0.72,
            ),
            "jarmin_field": VoiceProfile(
                profile_id="jarmin_field",
                title="Jarmin Saha",
                language="tr-TR",
                rate=0.94,
                pitch=0.96,
                volume=1.0,
                notification_level=0.90,
            ),
            "jarmin_quiet": VoiceProfile(
                profile_id="jarmin_quiet",
                title="Jarmin Sessiz Ortam",
                language="tr-TR",
                rate=0.90,
                pitch=0.98,
                volume=0.52,
                notification_level=0.35,
            ),
        }

    def get(
        self,
        profile_id: str,
    ) -> VoiceProfile:
        try:
            return self._profiles[
                profile_id
            ]
        except KeyError as error:
            raise KeyError(
                f"Ses profili bulunamadı: "
                f"{profile_id}"
            ) from error

    def list(
        self,
    ) -> list[dict[str, Any]]:
        return [
            profile.as_dict()
            for profile in self._profiles.values()
        ]

    def ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            self._profiles
        )