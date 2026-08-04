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
    SensorPacketState,
    SensorType,
)
from syk_core.runtime_kernel.session_manager import (
    RuntimeLocation,
    RuntimeSessionError,
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


def create_runtime() -> tuple[
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

    runtime = RuntimeCoordinator(
        clock=clock.now
    )

    return runtime, clock


def register_camera(
    runtime: RuntimeCoordinator,
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


def register_sonar(
    runtime: RuntimeCoordinator,
) -> None:
    runtime.register_sensor(
        SensorDescriptor(
            sensor_id="SONAR-1",
            name="Balık Bulucu Sonar",
            sensor_type=SensorType.SONAR,
            source="bluetooth",
            capabilities=(
                "derinlik",
                "su_kolonu",
                "hedef_yankısı",
            ),
        )
    )


def test_full_runtime_boot_is_healthy() -> None:
    runtime, _ = create_runtime()

    runtime.start()

    payload = runtime.health_snapshot()

    assert runtime.state is (
        RuntimeCoordinatorState.RUNNING
    )
    assert payload["koordinatör_durumu"] == (
        "çalışıyor"
    )
    assert payload["sağlıklı"] is True
    assert payload["kritik_sorun_sayısı"] == 0


def test_repeated_start_is_idempotent() -> None:
    runtime, _ = create_runtime()

    runtime.start()
    first_started_at = runtime.started_at

    runtime.start()

    assert runtime.state is (
        RuntimeCoordinatorState.RUNNING
    )
    assert runtime.started_at == first_started_at


def test_camera_to_sealed_evidence_flow() -> None:
    runtime, _ = create_runtime()
    runtime.start()
    register_camera(runtime)

    session = runtime.create_live_session(
        name="Arkeolojik yüzey incelemesi",
        metadata={
            "bölge": "Keban",
            "amaç": "yüzey analizi",
        },
    )

    runtime.add_session_pin(
        session.session_id,
        location=RuntimeLocation(
            latitude=38.802,
            longitude=38.741,
            accuracy_m=0.02,
            source="RTK",
        ),
        pin_type="araştırma_noktası",
        label="Yüzey gözlem noktası",
        confidence=0.98,
    )

    flow = runtime.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={
            "nesne": "taş yüzeyi",
            "işaret_adayı": True,
            "açıklama": "oyuk ve çizgi birleşimi",
        },
        evidence_type="yüzey_analizi",
        evidence_title="Taş yüzeyi gözlemi",
        quality_score=0.97,
        byte_count=8192,
        frame_count=1,
    )

    assert flow.packet_state == "kabul_edildi"
    assert flow.evidence_id is not None
    assert flow.report_block_id is not None

    evidence = runtime.approve_evidence(
        flow.evidence_id,
        actor="Bilge Kaan",
        seal=True,
        seal_actor="Kurucu Kaan",
    )

    assert evidence.state is EvidenceState.SEALED
    assert evidence.seal_hash is not None
    assert runtime.evidence_runtime.verify(
        evidence.evidence_id
    ) is True

    assert len(session.streams) == 1
    assert len(session.evidence_links) == 1
    assert len(session.map_pins) == 1


def test_sonar_fish_observation_flow() -> None:
    runtime, _ = create_runtime()
    runtime.start()
    register_sonar(runtime)

    session = runtime.create_live_session(
        name="Keban balık gözlemi"
    )

    flow = runtime.process_sensor_data(
        session_id=session.session_id,
        sensor_id="SONAR-1",
        payload={
            "derinlik_m": 14.8,
            "hedef_sayısı": 3,
            "tür_adayı": "sazan",
            "tür_güveni": 0.86,
        },
        evidence_type="balık_gözlemi",
        evidence_title="Sonar balık hedefleri",
        quality_score=0.91,
        byte_count=2048,
        frame_count=3,
    )

    assert flow.packet_state == "kabul_edildi"
    assert flow.evidence_id is not None

    evidence = runtime.evidence_runtime.get(
        flow.evidence_id
    )

    assert evidence.content["payload"][
        "tür_adayı"
    ] == "sazan"

    stream = next(
        iter(session.streams.values())
    )

    assert stream.stream_type.value == "sonar"
    assert stream.frame_count == 3


def test_second_active_session_is_rejected() -> None:
    runtime, _ = create_runtime()
    runtime.start()

    runtime.create_live_session(
        name="Birinci oturum"
    )

    with pytest.raises(
        RuntimeSessionError,
        match="yalnız bir",
    ):
        runtime.create_live_session(
            name="İkinci oturum"
        )


def test_offline_packet_is_buffered_and_recovered() -> None:
    runtime, _ = create_runtime()
    runtime.start()
    register_camera(runtime)

    session = runtime.create_live_session(
        name="Çevrimdışı tampon"
    )

    runtime.sensor_runtime.disconnect(
        "KAMERA-1",
        offline=True,
    )

    flow = runtime.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={
            "kare": 1,
            "açıklama": "çevrimdışı kayıt",
        },
        evidence_type="fotoğraf",
        evidence_title="Tamponlanan kare",
        quality_score=0.95,
    )

    assert flow.packet_state == (
        SensorPacketState.BUFFERED.value
    )
    assert flow.evidence_id is None
    assert len(
        runtime.sensor_runtime.buffered_packets
    ) == 1

    runtime.state = (
        RuntimeCoordinatorState.DEGRADED
    )

    runtime.recover()

    assert runtime.state is (
        RuntimeCoordinatorState.RUNNING
    )
    assert len(
        runtime.sensor_runtime.buffered_packets
    ) == 0
    assert len(
        runtime.sensor_runtime.accepted_packets
    ) == 1


def test_scheduler_and_runtime_events_propagate() -> None:
    runtime, _ = create_runtime()
    runtime.start()

    completed: list[str] = []

    runtime.scheduler.schedule_once(
        name="Runtime sağlık görevi",
        handler=lambda: completed.append(
            "tamamlandı"
        ),
    )

    count = runtime.run_scheduled_tasks()

    assert count == 1
    assert completed == ["tamamlandı"]

    topics = [
        event.topic
        for event in runtime.event_bus.history
    ]

    assert "runtime.coordinator.started" in topics
    assert (
        "runtime.scheduler.task.scheduled"
        in topics
    )
    assert (
        "runtime.scheduler.task.started"
        in topics
    )
    assert (
        "runtime.scheduler.task.completed"
        in topics
    )


def test_evidence_tampering_is_detected() -> None:
    runtime, _ = create_runtime()
    runtime.start()
    register_camera(runtime)

    session = runtime.create_live_session(
        name="Değişiklik kontrolü"
    )

    flow = runtime.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={
            "değer": 42,
        },
        evidence_type="ölçüm",
        evidence_title="Doğrulama kaydı",
        quality_score=0.96,
    )

    assert flow.evidence_id is not None
    assert runtime.evidence_runtime.verify(
        flow.evidence_id
    ) is True

    evidence = runtime.evidence_runtime.get(
        flow.evidence_id
    )

    evidence.content["payload"]["değer"] = 99

    assert runtime.evidence_runtime.verify(
        flow.evidence_id
    ) is False


def test_timeout_is_visible_in_health_snapshot() -> None:
    runtime, clock = create_runtime()
    runtime.start()

    runtime.create_live_session(
        name="Zaman aşımı oturumu",
        timeout=timedelta(minutes=5),
    )

    clock.advance(
        timedelta(minutes=6)
    )

    assert runtime.check_timeouts() == 1

    payload = runtime.health_snapshot()

    assert payload["toplam_sorun_sayısı"] == 1
    assert payload["sorunlar"][0][
        "bileşen"
    ] == "session_manager"
    assert payload["oturum_yöneticisi"][
        "zaman_aşımı_oturum_sayısı"
    ] == 1


def test_safe_stop_is_idempotent() -> None:
    runtime, _ = create_runtime()
    runtime.start()
    register_camera(runtime)

    session = runtime.create_live_session(
        name="Güvenli kapanış"
    )

    runtime.stop()
    first_stopped_at = runtime.stopped_at

    runtime.stop()

    assert runtime.state is (
        RuntimeCoordinatorState.STOPPED
    )
    assert runtime.stopped_at == first_stopped_at
    assert session.state.value == "tamamlandı"


def test_stopped_runtime_can_be_recovered() -> None:
    runtime, _ = create_runtime()

    runtime.start()
    runtime.stop()
    runtime.recover()

    assert runtime.state is (
        RuntimeCoordinatorState.RUNNING
    )
    assert runtime.kernel.state.value == (
        "çalışıyor"
    )


def test_common_snapshot_preserves_turkish_runtime() -> None:
    runtime, _ = create_runtime()
    runtime.start()
    register_camera(runtime)

    session = runtime.create_live_session(
        name="Türkçe çalışma oturumu"
    )

    runtime.process_sensor_data(
        session_id=session.session_id,
        sensor_id="KAMERA-1",
        payload={
            "açıklama": "bitki ve yüzey analizi",
            "tür_adayı": "meşe",
        },
        evidence_type="botanik",
        evidence_title="Türkçe gözlem",
        quality_score=0.98,
    )

    payload = runtime.health_snapshot()

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

    assert payload["oturum_yöneticisi"][
        "aktif_oturum_sayısı"
    ] == 1

    evidence_payload = payload[
        "kanıt_motoru"
    ]["kanıtlar"][0]

    assert evidence_payload["başlık"] == (
        "Türkçe gözlem"
    )

    assert evidence_payload["içerik"][
        "payload"
    ]["açıklama"] == (
        "bitki ve yüzey analizi"
    )
