from syk_jarmin.jarmin_core import (
    JarminCore,
)


def test_jarmin_oturumu_ve_komutu():
    core = JarminCore()

    session = core.create_session(
        session_id="JARMIN-TEST-001"
    )

    assert (
        session["status"]
        == "active"
    )

    result = core.process(
        session_id="JARMIN-TEST-001",
        text="görüntü modülünü aç",
    )

    assert (
        result.intent.intent_id
        == "open_module"
    )

    assert result.command.success

    assert (
        result.command.payload[
            "module_id"
        ]
        == "image"
    )

    assert len(
        result.response_sha256
    ) == 64


def test_onay_gerektiren_komut():
    core = JarminCore()

    core.create_session(
        session_id="JARMIN-TEST-002"
    )

    first = core.process(
        session_id="JARMIN-TEST-002",
        text="rapor oluştur",
    )

    assert not first.command.success
    assert (
        first.command
        .requires_confirmation
    )

    second = core.process(
        session_id="JARMIN-TEST-002",
        text="rapor oluştur",
        confirmed=True,
    )

    assert second.command.success


def test_konusma_hafizasi_korunur():
    core = JarminCore()

    core.create_session(
        session_id="JARMIN-TEST-003"
    )

    core.process(
        session_id="JARMIN-TEST-003",
        text="sistem durumu",
    )

    snapshot = core.session_snapshot(
        "JARMIN-TEST-003"
    )

    assert (
        snapshot["session"][
            "turn_count"
        ]
        == 1
    )

    assert (
        snapshot["conversation"][
            "message_count"
        ]
        == 2
    )