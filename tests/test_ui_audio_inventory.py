import wave

from syk_simulasyon.syk_ui import AudioManager


def test_ui_audio_inventory_is_ready():
    manager = AudioManager()

    assert manager.missing_files() == []
    assert manager.is_ready()

    for profile in manager.available():
        path = manager.select(profile.id)

        assert path.is_file()
        assert path.stat().st_size > 44

        with wave.open(str(path), "rb") as wav_file:
            assert wav_file.getnchannels() == 1
            assert wav_file.getsampwidth() == 2
            assert wav_file.getframerate() == 44_100
            assert wav_file.getnframes() > 0
