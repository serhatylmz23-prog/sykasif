from syk_jarmin.runtime.command_router import (
    CommandResult,
    CommandRouteResult,
    CommandRouter,
)


def test_komut_kaydedilir():
    router = CommandRouter()

    router.register(
        "durum",
        lambda **_: {
            "success": True,
            "message": "Hazır.",
        },
    )

    result = router.execute(
        "durum"
    )

    assert isinstance(
        result,
        CommandResult,
    )

    assert result.success
    assert result.message == "Hazır."


def test_varsayilan_modul_komutu():
    router = CommandRouter()

    result = router.execute(
        "open_module",
        entities={
            "module_id": "image",
        },
    )

    assert result.success

    assert (
        result.payload[
            "module_id"
        ]
        == "image"
    )


def test_onay_gerektiren_komut():
    router = CommandRouter()

    first = router.execute(
        "create_report",
        requires_confirmation=True,
        confirmed=False,
    )

    assert not first.success
    assert first.requires_confirmation

    second = router.execute(
        "create_report",
        requires_confirmation=True,
        confirmed=True,
    )

    assert second.success
    assert not second.requires_confirmation


def test_eski_sonuc_adi_korunur():
    assert (
        CommandRouteResult
        is CommandResult
    )


def test_router_snapshot_sha():
    router = CommandRouter()

    snapshot = router.snapshot()

    assert len(
        snapshot["snapshot_sha256"]
    ) == 64