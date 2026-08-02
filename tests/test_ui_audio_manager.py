from pathlib import Path

from syk_ui import AudioManager


def test_ui_audio_profiles_resolve_inside_static_audio():
    manager = AudioManager()

    expected = {
        "system": "system.wav",
        "notification": "notification.wav",
        "analysis": "analysis.wav",
        "evidence": "evidence.wav",
        "finance": "finance.wav",
        "jarmin": "jarmin.wav",
    }

    for profile_id, filename in expected.items():
        resolved = manager.select(profile_id)

        assert resolved.name == filename
        assert resolved.parent.name == "audio"
        assert resolved.parent.parent.name == "static"
        assert isinstance(resolved, Path)
