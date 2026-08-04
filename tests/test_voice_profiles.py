from syk_jarmin.voice_profiles import (
    VoiceProfileRegistry,
)


def test_turkce_ses_profilleri_var():
    registry = VoiceProfileRegistry()

    assert (
        "jarmin_default"
        in registry.ids()
    )

    assert (
        registry.get(
            "jarmin_field"
        ).language
        == "tr-TR"
    )