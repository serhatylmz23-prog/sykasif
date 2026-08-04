from datetime import UTC, datetime

from syk_simulasyon.syk_ui_runtime.mobile_sensor_runtime import (
    LocationReading,
    MobileSensorRuntime,
)


def test_kamera_baslatilir():
    runtime = MobileSensorRuntime()

    result = runtime.start_camera(
        facing_mode="environment",
        width=1280,
        height=720,
        frame_rate=24.0,
        stream_id="CAM-TEST-001",
    )

    assert result["active"]

    assert (
        result["facing_mode"]
        == "environment"
    )


def test_mikrofon_baslatilir():
    runtime = MobileSensorRuntime()

    result = runtime.start_microphone(
        sample_rate=16000,
        channels=1,
        stream_id="MIC-TEST-001",
    )

    assert result["active"]

    assert (
        result["sample_rate"]
        == 16000
    )


def test_konum_kaydi_alinir():
    runtime = MobileSensorRuntime()

    result = runtime.add_location(
        LocationReading(
            latitude=39.92077,
            longitude=32.85411,
            accuracy_meters=4.5,
            altitude_meters=938.0,
            heading_degrees=125.0,
            speed_meters_per_second=1.2,
            captured_at=datetime.now(
                UTC
            ).isoformat(),
            source="test",
        )
    )

    assert (
        result["latitude"]
        == 39.92077
    )

    assert (
        runtime.snapshot()[
            "location_count"
        ]
        == 1
    )


def test_kamera_karesi_kaydedilir():
    runtime = MobileSensorRuntime()

    result = runtime.capture_frame(
        device_id="PHONE-001",
        data=b"test-image-data",
        mime_type="image/jpeg",
        width=640,
        height=480,
    )

    assert (
        result["byte_count"]
        == len(
            b"test-image-data"
        )
    )

    assert len(
        result["frame_sha256"]
    ) == 64

    assert (
        result[
            "field_validation_required"
        ]
        is True
    )


def test_gecersiz_konum_reddedilir():
    runtime = MobileSensorRuntime()

    reading = LocationReading(
        latitude=120.0,
        longitude=32.0,
        accuracy_meters=2.0,
        altitude_meters=None,
        heading_degrees=None,
        speed_meters_per_second=None,
        captured_at=datetime.now(
            UTC
        ).isoformat(),
        source="test",
    )

    try:
        runtime.add_location(
            reading
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Geçersiz konum kabul edildi."
        )


def test_runtime_sha_uretir():
    runtime = MobileSensorRuntime()

    snapshot = runtime.snapshot()

    assert len(
        snapshot[
            "snapshot_sha256"
        ]
    ) == 64

    assert (
        snapshot[
            "native_sensor_bridge_ready"
        ]
        is False
    )