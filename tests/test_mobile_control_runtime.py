from syk_simulasyon.syk_ui_runtime.mobile_control_runtime import (
    MobileControlRuntime,
)


def test_mobil_kontrol_cihazi_kaydedilir():
    runtime = MobileControlRuntime()

    result = runtime.register(
        device_id="PHONE-006D-001",
        device_type="phone",
    )

    state = result["state"]

    assert (
        state["device_type"]
        == "phone"
    )

    assert (
        state["camera_state"]
        == "idle"
    )

    assert len(
        result["state_sha256"]
    ) == 64


def test_sensor_durumlari_guncellenir():
    runtime = MobileControlRuntime()

    runtime.register(
        device_id="TABLET-006D-001",
        device_type="tablet",
    )

    result = runtime.update(
        "TABLET-006D-001",
        camera_state="active",
        microphone_state="active",
        location_state="active",
        notification_permission=(
            "granted"
        ),
        connection_state="online",
        pairing_state="paired",
        offline_queue_count=3,
        fullscreen=True,
        wake_lock=True,
    )

    state = result["state"]

    assert (
        state["camera_state"]
        == "active"
    )

    assert (
        state["microphone_state"]
        == "active"
    )

    assert (
        state["location_state"]
        == "active"
    )

    assert (
        state[
            "notification_permission"
        ]
        == "granted"
    )

    assert (
        state["pairing_state"]
        == "paired"
    )

    assert (
        state[
            "offline_queue_count"
        ]
        == 3
    )

    assert state["fullscreen"]
    assert state["wake_lock"]


def test_gecersiz_durum_reddedilir():
    runtime = MobileControlRuntime()

    runtime.register(
        device_id="PHONE-006D-002",
        device_type="phone",
    )

    try:
        runtime.update(
            "PHONE-006D-002",
            camera_state=(
                "gecersiz"
            ),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Geçersiz kamera durumu "
            "kabul edildi."
        )


def test_kontrol_durumu_sifirlanir():
    runtime = MobileControlRuntime()

    runtime.register(
        device_id="TABLET-006D-002",
        device_type="tablet",
    )

    runtime.update(
        "TABLET-006D-002",
        camera_state="active",
        microphone_state="active",
        fullscreen=True,
    )

    result = runtime.reset(
        "TABLET-006D-002"
    )

    state = result["state"]

    assert (
        state["camera_state"]
        == "idle"
    )

    assert (
        state["microphone_state"]
        == "idle"
    )

    assert not state["fullscreen"]


def test_runtime_snapshot_sha():
    runtime = MobileControlRuntime()

    runtime.register(
        device_id="PHONE-006D-003",
        device_type="phone",
    )

    snapshot = runtime.snapshot()

    assert (
        snapshot["device_count"]
        == 1
    )

    assert len(
        snapshot[
            "snapshot_sha256"
        ]
    ) == 64