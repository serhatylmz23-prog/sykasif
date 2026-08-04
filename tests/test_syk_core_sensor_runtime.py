from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_kernel import (
    RuntimeEventBus,
    RuntimeSessionManager,
    SensorConnectionState,
    SensorDescriptor,
    SensorPacketState,
    SensorRuntime,
    SensorRuntimeError,
    SensorType,
)


class ManualClock:
    def __init__(
        self,
        current: datetime,
    ) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def advance(
        self,
        delta: timedelta,
    ) -> None:
        self.current += delta


def create_runtime(
    *,
    buffer_limit: int = 10,
) -> tuple[
    SensorRuntime,
    RuntimeSessionManager,
    ManualClock,
]:
    clock = ManualClock(
        datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=UTC,
        )
    )

    event_bus = RuntimeEventBus()

    session_manager = RuntimeSessionManager(
        event_bus=event_bus,
        clock=clock.now,
    )

    runtime = SensorRuntime(
        event_bus=event_bus,
        session_manager=session_manager,
        clock=clock.now,
        offline_buffer_limit=buffer_limit,
    )

    return runtime, session_manager, clock


def register_camera(
    runtime: SensorRuntime,
) -> None:
    runtime.register_sensor(
        SensorDescriptor(
            sensor_id="KAMERA-1",
            name="Yılan Kamera",
            sensor_type=SensorType.CAMERA,
            source="usb",
            capabilities=(
                "fotoğraf",
                "video",
                "canlı_akış",
            ),
        )
    )


def test_sensor_registration() -> None:
    runtime, _, _ = create_runtime()

    device = runtime.register_sensor(
        SensorDescriptor(
            sensor_id="PROB-1",
            name="SYK PROBE",
            sensor_type=SensorType.PROBE,
            source="usb",
        )
    )

    assert device.descriptor.sensor_id == "PROB-1"
    assert device.connection_state is (
        SensorConnectionState.REGISTERED
    )


def test_duplicate_sensor_is_rejected() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)

    with pytest.raises(
        SensorRuntimeError,
        match="zaten kayıtlı",
    ):
        register_camera(runtime)


def test_sensor_connect_and_disconnect() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)

    device = runtime.connect("KAMERA-1")

    assert device.connection_state is (
        SensorConnectionState.CONNECTED
    )
    assert device.connected_at is not None

    runtime.disconnect(
        "KAMERA-1",
        reason="kablo çıkarıldı",
    )

    assert device.connection_state is (
        SensorConnectionState.DISCONNECTED
    )
    assert device.last_error == "kablo çıkarıldı"


def test_connected_sensor_accepts_good_packet() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    record = runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"nesne": "bitki"},
        quality_score=0.92,
        byte_count=2048,
        frame_count=1,
    )

    assert record.state is (
        SensorPacketState.ACCEPTED
    )
    assert len(runtime.accepted_packets) == 1


def test_low_quality_packet_is_rejected() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    record = runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"nesne": "belirsiz"},
        quality_score=0.45,
    )

    assert record.state is (
        SensorPacketState.REJECTED
    )
    assert len(runtime.rejected_packets) == 1


def test_very_low_quality_packet_is_quarantined() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    record = runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"nesne": "gürültü"},
        quality_score=0.15,
    )

    assert record.state is (
        SensorPacketState.QUARANTINED
    )
    assert len(runtime.quarantined_packets) == 1


def test_empty_packet_is_quarantined() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    record = runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={},
        quality_score=0.90,
    )

    assert record.state is (
        SensorPacketState.QUARANTINED
    )
    assert "boş" in str(record.reason)


def test_offline_packet_is_buffered() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)

    record = runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"kare": 1},
        quality_score=0.90,
    )

    assert record.state is (
        SensorPacketState.BUFFERED
    )
    assert len(runtime.buffered_packets) == 1


def test_offline_buffer_limit_rejects_packet() -> None:
    runtime, _, _ = create_runtime(
        buffer_limit=1
    )
    register_camera(runtime)

    runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"kare": 1},
    )

    record = runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"kare": 2},
    )

    assert record.state is (
        SensorPacketState.REJECTED
    )
    assert "tampon dolu" in str(record.reason)


def test_reconnect_flushes_offline_buffer() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)

    runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"kare": 1},
        quality_score=0.95,
    )

    device = runtime.reconnect("KAMERA-1")

    assert device.connection_state is (
        SensorConnectionState.CONNECTED
    )
    assert device.reconnect_count == 1
    assert len(runtime.buffered_packets) == 0
    assert len(runtime.accepted_packets) == 1


def test_packet_updates_session_stream() -> None:
    runtime, sessions, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    session = sessions.create_session(
        name="Saha oturumu"
    )
    sessions.start(session.session_id)

    runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"nesne": "bitki"},
        quality_score=0.95,
        byte_count=4096,
        frame_count=2,
        session_id=session.session_id,
    )

    assert len(session.streams) == 1

    stream = next(
        iter(session.streams.values())
    )

    assert stream.frame_count == 2
    assert stream.byte_count == 4096


def test_packet_links_evidence_to_session() -> None:
    runtime, sessions, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    session = sessions.create_session(
        name="Kanıt oturumu"
    )
    sessions.start(session.session_id)

    runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"nesne": "yazıt"},
        quality_score=0.97,
        session_id=session.session_id,
        evidence_id="KANIT-001",
    )

    assert len(session.evidence_links) == 1
    assert session.evidence_links[0].evidence_id == (
        "KANIT-001"
    )


def test_session_link_requires_session_manager() -> None:
    runtime = SensorRuntime()

    runtime.register_sensor(
        SensorDescriptor(
            sensor_id="SONAR-1",
            name="Sonar",
            sensor_type=SensorType.SONAR,
            source="usb",
        )
    )

    runtime.connect("SONAR-1")

    with pytest.raises(
        SensorRuntimeError,
        match="Session Manager",
    ):
        runtime.submit_packet(
            sensor_id="SONAR-1",
            payload={"derinlik": 12.4},
            quality_score=0.90,
            session_id="OTURUM-YOK",
        )


def test_failed_sensor_is_marked() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)

    device = runtime.fail_sensor(
        "KAMERA-1",
        reason="donanım yanıt vermiyor",
    )

    assert device.connection_state is (
        SensorConnectionState.FAILED
    )
    assert device.last_error == (
        "donanım yanıt vermiyor"
    )


def test_connected_sensor_cannot_be_unregistered() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    with pytest.raises(
        SensorRuntimeError,
        match="Bağlı sensör",
    ):
        runtime.unregister_sensor("KAMERA-1")


def test_snapshot_preserves_turkish_keys() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"açıklama": "bitki analizi"},
        quality_score=0.98,
    )

    payload = runtime.snapshot()

    assert payload["toplam_sensör_sayısı"] == 1
    assert payload["bağlı_sensör_sayısı"] == 1
    assert payload[
        "kabul_edilen_paket_sayısı"
    ] == 1
    assert payload["sensörler"][0][
        "bağlantı_durumu"
    ] == "bağlı"


def test_sensor_events_are_published() -> None:
    runtime, _, _ = create_runtime()
    register_camera(runtime)
    runtime.connect("KAMERA-1")

    runtime.submit_packet(
        sensor_id="KAMERA-1",
        payload={"kare": 1},
        quality_score=0.95,
    )

    runtime.disconnect(
        "KAMERA-1",
        offline=True,
    )

    topics = [
        event.topic
        for event in runtime.event_bus.history
    ]

    assert "runtime.sensor.registered" in topics
    assert "runtime.sensor.connected" in topics
    assert (
        "runtime.sensor.packet.accepted"
        in topics
    )
    assert "runtime.sensor.offline" in topics
