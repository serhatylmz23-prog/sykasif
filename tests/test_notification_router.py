from syk_jarmin.runtime.notification_router import (
    NotificationRouter,
)


def test_bildirim_yonlendirici_import_edilir():
    router = NotificationRouter()

    result = router.route(
        event_type="analysis_completed",
        message="Analiz tamamlandı.",
    )

    assert (
        result.event_type
        == "analysis_completed"
    )

    assert (
        result.level
        == "success"
    )

    assert len(
        result.notification_sha256
    ) == 64


def test_kritik_bildirim_uretilir():
    router = NotificationRouter()

    result = router.route(
        event_type="critical_event",
        message="Kritik olay algılandı.",
    )

    assert (
        result.level
        == "critical"
    )

    assert (
        result.sound_profile
        == "kasif_critical"
    )


def test_bildirim_bekleyen_listesine_girer():
    router = NotificationRouter()

    record = router.route(
        event_type="evidence_created",
        message="Kanıt oluşturuldu.",
    )

    pending = router.pending()

    assert len(pending) == 1

    router.acknowledge(
        record.notification_id
    )

    assert router.pending() == []


def test_bildirim_snapshot_sha_uretir():
    router = NotificationRouter()

    snapshot = router.snapshot()

    assert len(
        snapshot["snapshot_sha256"]
    ) == 64