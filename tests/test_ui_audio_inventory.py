from syk_ui import AudioManager


def test_ui_audio_inventory_reports_missing_real_files():
    manager = AudioManager()

    missing = manager.missing_files()

    assert len(missing) == 6
    assert not manager.is_ready()
    assert {path.name for path in missing} == {
        "system.wav",
        "notification.wav",
        "analysis.wav",
        "evidence.wav",
        "finance.wav",
        "jarmin.wav",
    }
