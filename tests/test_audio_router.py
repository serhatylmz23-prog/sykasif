from syk_jarmin.audio_router import (
    AudioRouter,
)


def test_ses_komutu_jarmin_icin_hazirlanir():
    result = AudioRouter().receive(
        "Jarmin, finans özeti"
        .encode("utf-8")
    )

    assert result.wake_word.detected

    assert (
        result.command_text
        == "finans özeti"
    )

    assert (
        result.as_dict()[
            "ready_for_jarmin"
        ]
    )


def test_jarmin_yaniti_seslendirilir():
    result = AudioRouter().respond(
        "İşlem tamamlandı."
    )

    assert result.audio