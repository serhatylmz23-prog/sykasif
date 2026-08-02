from __future__ import annotations

import math
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO_ROOT = ROOT / "src" / "syk_ui" / "static" / "audio"

SAMPLE_RATE = 44_100
AMPLITUDE = 0.28

TONES = {
    "system.wav": (440.0, 0.18),
    "notification.wav": (660.0, 0.22),
    "analysis.wav": (520.0, 0.30),
    "evidence.wav": (784.0, 0.34),
    "finance.wav": (880.0, 0.26),
    "jarmin.wav": (392.0, 0.24),
}


def generate_tone(path: Path, frequency: float, duration: float) -> None:
    frame_count = int(SAMPLE_RATE * duration)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)

        frames = bytearray()

        for index in range(frame_count):
            attack = index / max(1, int(SAMPLE_RATE * 0.02))
            release = (frame_count - index) / max(
                1,
                int(SAMPLE_RATE * 0.04),
            )
            envelope = max(0.0, min(1.0, attack, release))

            sample = math.sin(
                2.0 * math.pi * frequency * index / SAMPLE_RATE
            )
            value = int(32767 * AMPLITUDE * envelope * sample)
            frames.extend(struct.pack("<h", value))

        wav_file.writeframes(frames)


def main() -> None:
    AUDIO_ROOT.mkdir(parents=True, exist_ok=True)

    for filename, parameters in TONES.items():
        frequency, duration = parameters
        generate_tone(
            AUDIO_ROOT / filename,
            frequency,
            duration,
        )

    print("SPR_003_UI_0021_AUDIO_ASSETS_OK")


if __name__ == "__main__":
    main()
