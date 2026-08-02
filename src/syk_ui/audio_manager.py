from dataclasses import dataclass
from pathlib import Path


AUDIO_ROOT = Path(__file__).resolve().parent / "static" / "audio"


@dataclass(frozen=True)
class AudioProfile:
    id: str
    filename: str


PROFILES = {
    "system": AudioProfile("system", "system.wav"),
    "notification": AudioProfile("notification", "notification.wav"),
    "analysis": AudioProfile("analysis", "analysis.wav"),
    "evidence": AudioProfile("evidence", "evidence.wav"),
    "finance": AudioProfile("finance", "finance.wav"),
    "jarmin": AudioProfile("jarmin", "jarmin.wav"),
}


class AudioManager:
    def __init__(self):
        self._current = "system"

    @property
    def current(self) -> AudioProfile:
        return PROFILES[self._current]

    def select(self, profile_id: str) -> Path:
        if profile_id not in PROFILES:
            raise KeyError(f"Unknown audio profile: {profile_id}")

        self._current = profile_id
        return AUDIO_ROOT / self.current.filename

    def available(self) -> list[AudioProfile]:
        return list(PROFILES.values())
