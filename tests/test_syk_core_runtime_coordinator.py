from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_kernel.coordinator import (
    RuntimeCoordinator,
    RuntimeCoordinatorError,
    RuntimeCoordinatorState,
)
from syk_core.runtime_kernel.evidence_runtime import (
    EvidenceState,
)
from syk_core.runtime_kernel.sensor_runtime import (
    SensorDescriptor,
    SensorType,
)
from syk_core.runtime_kernel.session_manager import (
    RuntimeLocation,
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


def create_coordinator() -> tuple[
    RuntimeCoordinator,
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

    coordinator = RuntimeCoordinator(
        clock=clock.now
    )

    return coordinator, clock


def register_camera(
    coordinator: RuntimeCoordinator,
) -> None:
    coordinator.register_sensor(
        SensorDescriptor(
            sensor_id="KAMERA-1",
            name="Yılan Kamera",
            sensor_type=SensorType.CAMERA,
            source="usb",
        )
    )


def test_coordinator_starts_runtime() -> None:
    coordinator, _ = create_coordinator()

    coordinator.start()

    assert coordinator.state is (
        RuntimeCoordinatorState.RUNNING
    )
    assert coordinator.started_at is not None
    assert coordinator.kernel.state.value == (
        "çalışıyor"
    )


def test_runtime_operation_requires_start() -> None:
    coordinator, _ = create_coordinator()

    with pytest.raises(
        RuntimeCoordinatorError,
        match="çalışıyor olmalıdır",
    ):
        coordinator.create_live_session(
            name="Başlatılmamış"
        )


def test_register_sensor_and_create_session() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()

    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Keban saha oturumu",
        session_id="OTURUM-1",
    )

    sensor = coordinator.sensor_runtime.get_sensor(
        "KAMERA-1"
    )

    assert session.session_id == "OTURUM-1"
    assert session.state.value == "aktif"
    assert sensor.connection_state.value == "bağlı"


def test_dynamic_map_pin_is_added() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()

    session = coordinator.create_live_session(
        name="Harita oturumu"
    )

    pin = coordinator.add_session_pin(
        session.session_id,
        location=RuntimeLocation(
            latitude=38.802,
            longitude=38.741,
            accuracy_m=0.02,
            source="RTK",
        ),
        pin_type="araştırma_noktası",
        label="Keban kıyısı",
        confidence=0.97,
    )

    assert pin.label == "Keban kıyısı"
    assert pin.location.source == "RTK"
    assert pin.confidence == 0.97


def test_end_to_end_sensor_evidence_flow() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Bitki analizi"
    )

    result = coordinator.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={
            "tür_adayı": "meşe",
            "yaprak_güveni": 0.94,
        },
        evidence_type="botanik",
        evidence_title="Bitki türü gözlemi",
        quality_score=0.95,
        byte_count=4096,
        frame_count=1,
    )

    assert result.packet_state == "kabul_edildi"
    assert result.evidence_id is not None
    assert result.evidence_state == (
        "inceleme_bekliyor"
    )
    assert result.report_block_id is not None
    assert len(session.streams) == 1
    assert len(session.evidence_links) == 1


def test_rejected_packet_creates_no_evidence() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Düşük kalite"
    )

    result = coordinator.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={"nesne": "belirsiz"},
        evidence_type="görüntü",
        evidence_title="Belirsiz kare",
        quality_score=0.40,
    )

    assert result.packet_state == "reddedildi"
    assert result.evidence_id is None
    assert result.report_block_id is None


def test_quarantined_packet_creates_evidence() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Karantina"
    )

    result = coordinator.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={"nesne": "gürültü"},
        evidence_type="görüntü",
        evidence_title="Gürültülü kare",
        quality_score=0.15,
    )

    assert result.packet_state == (
        "karantinaya_alındı"
    )
    assert result.evidence_id is not None

    record = coordinator.evidence_runtime.get(
        result.evidence_id
    )

    assert record.state is EvidenceState.QUARANTINED


def test_evidence_can_be_approved_and_sealed() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Kanıt onayı"
    )

    result = coordinator.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={"nesne": "yazıt"},
        evidence_type="arkeoloji",
        evidence_title="Taş yazıt",
        quality_score=0.98,
    )

    assert result.evidence_id is not None

    record = coordinator.approve_evidence(
        result.evidence_id,
        actor="Bilge Kaan",
        seal=True,
        seal_actor="Kurucu Kaan",
    )

    assert record.state is EvidenceState.SEALED
    assert record.seal_hash is not None


def test_scheduler_runs_through_coordinator() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()

    results: list[str] = []

    coordinator.scheduler.schedule_once(
        name="sağlık kontrolü",
        handler=lambda: results.append(
            "tamam"
        ),
    )

    count = coordinator.run_scheduled_tasks()

    assert count == 1
    assert results == ["tamam"]


def test_session_timeout_creates_issue() -> None:
    coordinator, clock = create_coordinator()
    coordinator.start()

    coordinator.create_live_session(
        name="Zaman aşımı",
        timeout=timedelta(minutes=5),
    )

    clock.advance(timedelta(minutes=6))

    expired_count = coordinator.check_timeouts()

    assert expired_count == 1
    assert len(coordinator.issues) == 1
    assert coordinator.issues[0].severity == "uyarı"


def test_safe_stop_closes_runtime() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Kapanış"
    )

    coordinator.stop()

    sensor = coordinator.sensor_runtime.get_sensor(
        "KAMERA-1"
    )

    assert coordinator.state is (
        RuntimeCoordinatorState.STOPPED
    )
    assert session.state.value == "tamamlandı"
    assert sensor.connection_state.value == (
        "bağlantı_kesildi"
    )


def test_recover_reconnects_offline_sensor() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    coordinator.sensor_runtime.disconnect(
        "KAMERA-1",
        offline=True,
    )

    coordinator.state = (
        RuntimeCoordinatorState.DEGRADED
    )

    coordinator.recover()

    sensor = coordinator.sensor_runtime.get_sensor(
        "KAMERA-1"
    )

    assert coordinator.state is (
        RuntimeCoordinatorState.RUNNING
    )
    assert sensor.connection_state.value == "bağlı"
    assert sensor.reconnect_count == 1


def test_health_snapshot_preserves_turkish() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Türkçe sağlık"
    )

    coordinator.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={
            "açıklama": "bitki analizi",
        },
        evidence_type="botanik",
        evidence_title="Türkçe kanıt",
        quality_score=0.97,
    )

    payload = coordinator.health_snapshot()

    assert payload["koordinatör_durumu"] == (
        "çalışıyor"
    )
    assert payload["sağlıklı"] is True
    assert payload["akış_sayısı"] == 1
    assert payload["sensör_motoru"][
        "bağlı_sensör_sayısı"
    ] == 1
    assert payload["kanıt_motoru"][
        "toplam_kanıt_sayısı"
    ] == 1


def test_coordinator_events_are_published() -> None:
    coordinator, _ = create_coordinator()
    coordinator.start()
    register_camera(coordinator)

    session = coordinator.create_live_session(
        name="Olay akışı"
    )

    coordinator.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={"nesne": "balık"},
        evidence_type="balık",
        evidence_title="Balık gözlemi",
        quality_score=0.93,
    )

    coordinator.stop()

    topics = [
        event.topic
        for event in coordinator.event_bus.history
    ]

    assert "runtime.coordinator.started" in topics
    assert (
        "runtime.coordinator.flow.completed"
        in topics
    )
    assert "runtime.coordinator.stopped" in topics
