from syk_simulasyon.syk_ui_runtime.mobile_device_runtime import (
    DeviceCapabilities,
    DeviceViewport,
    MobileDeviceRuntime,
)


def _capabilities(
    *,
    touch: bool = True,
) -> DeviceCapabilities:
    return DeviceCapabilities(
        touch=touch,
        camera=True,
        microphone=True,
        location=True,
        notification=True,
        vibration=True,
        fullscreen=True,
        wake_lock=True,
        online=True,
        input_mode=(
            "touch"
            if touch
            else "mouse"
        ),
    )


def test_telefon_turu_algilanir():
    result = (
        MobileDeviceRuntime
        .detect_type(
            width=390,
            height=844,
            touch=True,
        )
    )

    assert result == "phone"


def test_tablet_turu_algilanir():
    result = (
        MobileDeviceRuntime
        .detect_type(
            width=1280,
            height=800,
            touch=True,
        )
    )

    assert result == "tablet"


def test_telefon_kaydi_ve_yerlesimi():
    runtime = MobileDeviceRuntime()

    result = runtime.register(
        device_id="PHONE-006A-001",
        device_type="phone",
        title="Saha Telefonu",
        platform="Android",
        user_agent="test",
        language="tr-TR",
        timezone="Europe/Istanbul",
        viewport=DeviceViewport(
            width=390,
            height=844,
            pixel_ratio=3.0,
            orientation="portrait",
        ),
        capabilities=_capabilities(),
    )

    assert (
        result["device"][
            "device_type"
        ]
        == "phone"
    )

    assert (
        result["layout"][
            "panel_mode"
        ]
        == "single_panel"
    )

    assert (
        result["layout"][
            "navigation_mode"
        ]
        == "bottom_navigation"
    )

    assert len(
        result["device"][
            "record_sha256"
        ]
    ) == 64


def test_yatay_tablet_cift_panel():
    runtime = MobileDeviceRuntime()

    result = runtime.register(
        device_id="TABLET-006A-001",
        device_type="tablet",
        title="Saha Tableti",
        platform="Android",
        user_agent="test",
        language="tr-TR",
        timezone="Europe/Istanbul",
        viewport=DeviceViewport(
            width=1280,
            height=800,
            pixel_ratio=2.0,
            orientation="landscape",
        ),
        capabilities=_capabilities(),
    )

    assert (
        result["layout"][
            "panel_mode"
        ]
        == "dual_panel"
    )

    assert (
        result["layout"][
            "columns"
        ]
        == 2
    )


def test_cihaz_gorunumu_guncellenir():
    runtime = MobileDeviceRuntime()

    runtime.register(
        device_id="TABLET-006A-002",
        device_type="tablet",
        title="Saha Tableti",
        platform="Android",
        user_agent="test",
        language="tr-TR",
        timezone="Europe/Istanbul",
        viewport=DeviceViewport(
            width=800,
            height=1280,
            pixel_ratio=2.0,
            orientation="portrait",
        ),
        capabilities=_capabilities(),
    )

    updated = runtime.update_viewport(
        "TABLET-006A-002",
        viewport=DeviceViewport(
            width=1280,
            height=800,
            pixel_ratio=2.0,
            orientation="landscape",
        ),
    )

    assert (
        updated["layout"][
            "orientation"
        ]
        == "landscape"
    )

    assert (
        updated["layout"][
            "columns"
        ]
        == 2
    )


def test_runtime_sha_uretir():
    runtime = MobileDeviceRuntime()

    snapshot = runtime.snapshot()

    assert len(
        snapshot[
            "snapshot_sha256"
        ]
    ) == 64

    assert (
        snapshot[
            "native_android_bridge_ready"
        ]
        is False
    )