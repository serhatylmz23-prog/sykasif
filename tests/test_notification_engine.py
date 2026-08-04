from syk_jarmin.notification_engine import (
    NotificationEngine,
)


def test_guvenli_bildirim_uretilir():
    engine = NotificationEngine()

    result = engine.create(
        level="critical",
        title="SyKaşif Uyarısı",
        message=(
            "Dikkat gerektiren olay bulundu."
        ),
        encrypted_hint=True,
    )

    assert (
        result.sound_id
        == "jarmin_secure_alert"
    )

    assert result.encrypted_hint

    assert len(
        result.sha256
    ) == 64


def test_bildirim_onaylanir():
    engine = NotificationEngine()

    created = engine.create(
        level="information",
        title="Bilgi",
        message="İşlem hazır.",
    )

    acknowledged = (
        engine.acknowledge(
            created.notification_id
        )
    )

    assert acknowledged.acknowledged