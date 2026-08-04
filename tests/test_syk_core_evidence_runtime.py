from __future__ import annotations

from datetime import UTC, datetime

import pytest

from syk_core.runtime_kernel import (
    EvidenceRuntime,
    EvidenceRuntimeError,
    EvidenceSource,
    EvidenceState,
    RuntimeEventBus,
    RuntimeSessionManager,
    SensorPacket,
    SensorPacketRecord,
    SensorPacketState,
)


class ManualClock:
    def __init__(
        self,
        current: datetime,
    ) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


def create_runtime() -> tuple[
    EvidenceRuntime,
    RuntimeSessionManager,
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

    sessions = RuntimeSessionManager(
        event_bus=event_bus,
        clock=clock.now,
    )

    runtime = EvidenceRuntime(
        event_bus=event_bus,
        session_manager=sessions,
        clock=clock.now,
    )

    return runtime, sessions


def source(
    *,
    source_id: str = "KAYNAK-1",
    session_id: str | None = None,
) -> EvidenceSource:
    return EvidenceSource(
        source_type="fotoğraf",
        source_id=source_id,
        session_id=session_id,
    )


def test_create_evidence_requires_review() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_id="KANIT-1",
        evidence_type="fotoğraf",
        title="Taş yüzeyi",
        content={"nesne": "yazıt"},
        source=source(),
        confidence_score=0.92,
    )

    assert record.state is (
        EvidenceState.PENDING_REVIEW
    )
    assert len(record.content_hash) == 64
    assert len(record.revisions) == 1


def test_duplicate_content_is_rejected() -> None:
    runtime, _ = create_runtime()

    runtime.create(
        evidence_type="fotoğraf",
        title="Aynı içerik",
        content={"değer": 1},
        source=source(),
    )

    with pytest.raises(
        EvidenceRuntimeError,
        match="daha önce",
    ):
        runtime.create(
            evidence_type="fotoğraf",
            title="Aynı içerik",
            content={"değer": 1},
            source=source(),
        )


def test_low_confidence_is_quarantined() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="kamera",
        title="Belirsiz görüntü",
        content={"nesne": "bilinmiyor"},
        source=source(),
        confidence_score=0.15,
    )

    assert record.state is (
        EvidenceState.QUARANTINED
    )
    assert record.quarantined_reason is not None


def test_release_from_quarantine() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="kamera",
        title="Belirsiz",
        content={"nesne": "işaret"},
        source=source(),
        confidence_score=0.10,
    )

    runtime.release_from_quarantine(
        record.evidence_id,
        actor="Bilge Kaan",
        reason="Uzman incelemesine açıldı.",
    )

    assert record.state is (
        EvidenceState.PENDING_REVIEW
    )
    assert record.quarantined_reason is None


def test_approve_and_seal_evidence() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Yazıt",
        content={"metin": "örnek"},
        source=source(),
        confidence_score=0.96,
    )

    runtime.approve(
        record.evidence_id,
        actor="Bilge Kaan",
    )

    runtime.seal(
        record.evidence_id,
        actor="Kurucu Kaan",
    )

    assert record.state is EvidenceState.SEALED
    assert record.approved_by == "Bilge Kaan"
    assert record.seal_hash is not None
    assert len(record.seal_hash) == 64
    assert runtime.verify(
        record.evidence_id
    ) is True


def test_sealed_evidence_is_immutable() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Mühür",
        content={"değer": 1},
        source=source(),
    )

    runtime.approve(
        record.evidence_id,
        actor="Bilge Kaan",
    )

    runtime.seal(
        record.evidence_id,
        actor="Kurucu Kaan",
    )

    with pytest.raises(
        EvidenceRuntimeError,
        match="değiştirilemez",
    ):
        runtime.update_metadata(
            record.evidence_id,
            actor="test",
            metadata={"değer": 2},
        )


def test_unapproved_evidence_cannot_be_sealed() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Bekleyen",
        content={"değer": 1},
        source=source(),
    )

    with pytest.raises(
        EvidenceRuntimeError,
        match="onaylanmış",
    ):
        runtime.seal(
            record.evidence_id,
            actor="Kurucu Kaan",
        )


def test_reject_evidence() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="sensör",
        title="Hatalı kayıt",
        content={"değer": 999},
        source=source(),
    )

    runtime.reject(
        record.evidence_id,
        actor="Uzman",
        reason="Kaynak doğrulanamadı.",
    )

    assert record.state is EvidenceState.REJECTED
    assert record.rejection_reason == (
        "Kaynak doğrulanamadı."
    )


def test_create_from_sensor_packet() -> None:
    runtime, _ = create_runtime()

    packet = SensorPacket(
        packet_id="PAKET-1",
        sensor_id="KAMERA-1",
        recorded_at=datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=UTC,
        ),
        payload={"nesne": "bitki"},
        quality_score=0.91,
    )

    packet_record = SensorPacketRecord(
        packet=packet,
        state=SensorPacketState.ACCEPTED,
        reason=None,
        processed_at=packet.recorded_at,
    )

    record = runtime.create_from_sensor_packet(
        packet_record,
        evidence_type="botanik",
        title="Bitki gözlemi",
    )

    assert record.source.sensor_id == "KAMERA-1"
    assert record.source.packet_id == "PAKET-1"
    assert record.content["payload"][
        "nesne"
    ] == "bitki"


def test_rejected_packet_cannot_create_evidence() -> None:
    runtime, _ = create_runtime()

    packet = SensorPacket(
        packet_id="PAKET-RED",
        sensor_id="PROB-1",
        recorded_at=datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=UTC,
        ),
        payload={"değer": 1},
    )

    packet_record = SensorPacketRecord(
        packet=packet,
        state=SensorPacketState.REJECTED,
        reason="kalite düşük",
        processed_at=packet.recorded_at,
    )

    with pytest.raises(
        EvidenceRuntimeError,
        match="Reddedilmiş",
    ):
        runtime.create_from_sensor_packet(
            packet_record
        )


def test_quarantined_packet_creates_quarantined_evidence() -> None:
    runtime, _ = create_runtime()

    packet = SensorPacket(
        packet_id="PAKET-KARANTINA",
        sensor_id="SONAR-1",
        recorded_at=datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=UTC,
        ),
        payload={"derinlik": 8.2},
        quality_score=0.20,
    )

    packet_record = SensorPacketRecord(
        packet=packet,
        state=SensorPacketState.QUARANTINED,
        reason="gürültülü sinyal",
        processed_at=packet.recorded_at,
    )

    record = runtime.create_from_sensor_packet(
        packet_record
    )

    assert record.state is (
        EvidenceState.QUARANTINED
    )
    assert record.quarantined_reason == (
        "gürültülü sinyal"
    )


def test_evidence_links_to_session() -> None:
    runtime, sessions = create_runtime()

    session = sessions.create_session(
        name="Kanıt oturumu"
    )
    sessions.start(session.session_id)

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Oturum kanıtı",
        content={"nesne": "taş"},
        source=source(
            session_id=session.session_id
        ),
    )

    assert len(session.evidence_links) == 1
    assert session.evidence_links[0].evidence_id == (
        record.evidence_id
    )


def test_verify_detects_content_tampering() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Kontrol",
        content={"değer": 1},
        source=source(),
    )

    assert runtime.verify(
        record.evidence_id
    ) is True

    record.content["değer"] = 2

    assert runtime.verify(
        record.evidence_id
    ) is False


def test_revision_chain_detects_tampering() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Sürüm kontrolü",
        content={"değer": 1},
        source=source(),
    )

    runtime.update_metadata(
        record.evidence_id,
        actor="Uzman",
        metadata={"açıklama": "kontrol edildi"},
    )

    assert runtime.verify(
        record.evidence_id
    ) is True

    record.revisions[1].details[
        "updated_keys"
    ] = ["değiştirildi"]

    assert runtime.verify(
        record.evidence_id
    ) is False


def test_report_block_is_created() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="termal",
        title="Termal sapma",
        content={"sıcaklık": 42.3},
        source=source(),
        confidence_score=0.88,
    )

    block = runtime.create_report_block(
        record.evidence_id,
        block_type="termal_analiz",
    )

    assert block.evidence_id == (
        record.evidence_id
    )
    assert block.payload["verified"] is True
    assert len(runtime.report_blocks) == 1


def test_snapshot_preserves_turkish_keys() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Türkçe kanıt",
        content={
            "açıklama": "yüzey işareti",
        },
        source=source(),
    )

    runtime.approve(
        record.evidence_id,
        actor="Bilge Kaan",
    )

    payload = runtime.snapshot()

    assert payload["toplam_kanıt_sayısı"] == 1
    assert payload["onaylanan_kanıt_sayısı"] == 1
    assert payload["kanıtlar"][0][
        "başlık"
    ] == "Türkçe kanıt"
    assert payload["kanıtlar"][0][
        "içerik"
    ]["açıklama"] == "yüzey işareti"


def test_evidence_events_are_published() -> None:
    runtime, _ = create_runtime()

    record = runtime.create(
        evidence_type="fotoğraf",
        title="Olay kanıtı",
        content={"değer": 1},
        source=source(),
    )

    runtime.approve(
        record.evidence_id,
        actor="Bilge Kaan",
    )

    runtime.create_report_block(
        record.evidence_id
    )

    runtime.seal(
        record.evidence_id,
        actor="Kurucu Kaan",
    )

    topics = [
        event.topic
        for event in runtime.event_bus.history
    ]

    assert "runtime.evidence.created" in topics
    assert "runtime.evidence.approved" in topics
    assert (
        "runtime.evidence.report_block.created"
        in topics
    )
    assert "runtime.evidence.sealed" in topics
