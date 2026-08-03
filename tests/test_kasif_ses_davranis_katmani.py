from syk_jarmin.audio_router import (
    AudioRouter,
)
from syk_jarmin.voice_profiles import (
    VoiceProfileRegistry,
)
from syk_jarmin.wake_word import (
    WakeWordEngine,
)


def test_kasif_uyandirma_sozcugu():
    result = WakeWordEngine().detect(
        "Kaşif, sistem durumunu göster"
    )

    assert result.detected
    assert result.wake_word == "Kaşif"
    assert (
        result.command_text
        == "sistem durumunu göster"
    )


def test_babus_uyandirma_sozcugu():
    result = WakeWordEngine().detect(
        "Babuş finans özetini aç"
    )

    assert result.detected
    assert result.wake_word == "Babuş"
    assert (
        result.command_text
        == "finans özetini aç"
    )


def test_eski_jarmin_adi_korunur():
    result = WakeWordEngine().detect(
        "Hey Jarmin sistem durumu"
    )

    assert result.detected
    assert result.wake_word == "Kaşif"


def test_kisik_seste_kullanici_konusur_kasif_yazar():
    router = AudioRouter(
        interaction_mode="low_voice"
    )

    plan = router.prepare_response(
        "Sistem hazır.",
        profile_id="kasif_quiet",
    )

    assert not plan.should_speak
    assert plan.should_display
    assert plan.synthesis is None


def test_sessiz_modda_sesli_ve_yazili_girdi_kabul_edilir():
    router = AudioRouter(
        interaction_mode="silent"
    )

    received = router.receive(
        "Kaşif sistem durumu".encode(
            "utf-8"
        )
    )

    plan = router.prepare_response(
        "Sistem hazır.",
        profile_id="kasif_silent",
    )

    assert received.wake_word.detected
    assert not plan.should_speak
    assert plan.should_display


def test_normal_mod_ses_paketi_uretir():
    router = AudioRouter()

    plan = router.prepare_response(
        "Kaşif hazır.",
        profile_id="kasif_default",
    )

    assert plan.should_speak
    assert plan.should_display
    assert plan.synthesis is not None
    assert plan.synthesis.audio


def test_eski_ses_profilleri_korunur():
    registry = VoiceProfileRegistry()

    assert (
        registry.get(
            "jarmin_default"
        ).profile_id
        == "kasif_default"
    )

    assert (
        registry.get(
            "jarmin_field"
        ).profile_id
        == "kasif_field"
    )