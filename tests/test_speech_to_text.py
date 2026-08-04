from syk_jarmin.speech_to_text import (
    SpeechToTextEngine,
)


def test_test_ses_verisi_metne_cevrilir():
    result = (
        SpeechToTextEngine()
        .transcribe(
            "Jarmin görüntüyü incele"
            .encode("utf-8")
        )
    )

    assert (
        result.text
        == "Jarmin görüntüyü incele"
    )

    assert result.simulated

    assert len(
        result.audio_sha256
    ) == 64


def test_bos_ses_reddedilir():
    try:
        (
            SpeechToTextEngine()
            .transcribe(b"")
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Boş ses kabul edildi."
        )