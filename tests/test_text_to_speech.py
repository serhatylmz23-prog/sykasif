from syk_jarmin.text_to_speech import (
    TextToSpeechEngine,
)


def test_turkce_metin_ses_paketi_uretir():
    result = (
        TextToSpeechEngine()
        .synthesize(
            "Görüntü analizi tamamlandı."
        )
    )

    assert result.audio

    assert result.preview_only

    assert len(
        result.audio_sha256
    ) == 64


def test_ses_profili_secilebilir():
    result = (
        TextToSpeechEngine()
        .synthesize(
            "Saha bildirimi",
            profile_id="jarmin_field",
        )
    )

    assert (
        result.profile_id
        == "jarmin_field"
    )