from syk_jarmin.wake_word import (
    WakeWordEngine,
)


def test_uyandirma_sozcugu_algilanir():
    result = WakeWordEngine().detect(
        "Hey Jarmin, sistem durumu"
    )

    assert result.detected

    assert (
        result.command_text
        == "sistem durumu"
    )


def test_uyandirma_sozcugu_yoksa():
    result = WakeWordEngine().detect(
        "sistem durumu"
    )

    assert not result.detected