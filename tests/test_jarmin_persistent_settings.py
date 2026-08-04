from pathlib import Path

from syk_jarmin.runtime.persistent_settings import (
    PersistentJarminSettings,
)


def test_jarmin_ayarlari_kalici(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "settings.json"
    )

    settings = (
        PersistentJarminSettings(
            path
        )
    )

    settings.update(
        language="tr-TR",
        voice_enabled=False,
        theme_mode="silver",
        voice_profile_id=(
            "jarmin_field"
        ),
    )

    reopened = (
        PersistentJarminSettings(
            path
        )
    )

    result = reopened.get()

    assert not result.voice_enabled

    assert (
        result.theme_mode
        == "silver"
    )

    assert (
        result.voice_profile_id
        == "jarmin_field"
    )


def test_ayar_sha_uretilir(
    tmp_path: Path,
):
    settings = (
        PersistentJarminSettings(
            tmp_path
            / "settings.json"
        )
    )

    snapshot = settings.snapshot()

    assert len(
        snapshot[
            "settings_sha256"
        ]
    ) == 64