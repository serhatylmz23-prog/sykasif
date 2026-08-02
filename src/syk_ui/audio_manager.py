from dataclasses import dataclass
from pathlib import Path


AUDIO_ROOT = Path(__file__).resolve().parent / "static" / "audio"


@dataclass(frozen=True)
class AudioProfile:
    id: str
    filename: str
    category: str
    required: bool = True


PROFILES = {
    "system": AudioProfile("system", "system.wav", "system"),
    "notification": AudioProfile("notification", "notification.wav", "notification"),
    "analysis": AudioProfile("analysis", "analysis.wav", "analysis"),
    "evidence": AudioProfile("evidence", "evidence.wav", "evidence"),
    "finance": AudioProfile("finance", "finance.wav", "finance"),
    "jarmin": AudioProfile("jarmin", "jarmin.wav", "voice"),
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

    def missing_files(self) -> list[Path]:
        return [
            AUDIO_ROOT / profile.filename
            for profile in PROFILES.values()
            if profile.required and not (AUDIO_ROOT / profile.filename).is_file()
        ]

    def is_ready(self) -> bool:
        return not self.missing_files()
