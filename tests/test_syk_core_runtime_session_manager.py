from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_kernel.event_bus import (
    RuntimeEventBus,
)
from syk_core.runtime_kernel.session_manager import (
    RuntimeLocation,
    RuntimeSessionError,
    RuntimeSessionManager,
    RuntimeSessionState,
    RuntimeStreamType,
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


def create_manager() -> tuple[
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

    manager = RuntimeSessionManager(
        event_bus=RuntimeEventBus(),
        clock=clock.now,
    )

    return manager, clock


def test_create_and_start_session() -> None:
    manager, _ = create_manager()

    session = manager.create_session(
        name="Keban saha oturumu",
        session_id="OTURUM-1",
    )

    manager.start(session.session_id)

    assert session.state is RuntimeSessionState.ACTIVE
    assert session.started_at is not None
    assert manager.snapshot()[
        "aktif_oturum_kimliği"
    ] == "OTURUM-1"


def test_duplicate_session_is_rejected() -> None:
    manager, _ = create_manager()

    manager.create_session(
        name="İlk",
        session_id="SABİT",
    )

    with pytest.raises(
        RuntimeSessionError,
        match="zaten kayıtlı",
    ):
        manager.create_session(
            name="İkinci",
            session_id="SABİT",
        )


def test_only_one_session_can_be_active() -> None:
    manager, _ = create_manager()

    first = manager.create_session(name="Bir")
    second = manager.create_session(name="İki")

    manager.start(first.session_id)

    with pytest.raises(
        RuntimeSessionError,
        match="yalnız bir",
    ):
        manager.start(second.session_id)


def test_pause_and_resume_session() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Canlı")
    manager.start(session.session_id)
    manager.pause(session.session_id)

    assert session.state is RuntimeSessionState.PAUSED
    assert session.pause_count == 1

    manager.resume(session.session_id)

    assert session.state is RuntimeSessionState.ACTIVE


def test_attach_and_record_camera_stream() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Kamera")
    manager.start(session.session_id)

    stream = manager.attach_stream(
        session.session_id,
        stream_type=RuntimeStreamType.CAMERA,
        source="yılan_kamera",
        stream_id="KAMERA-1",
    )

    manager.record_stream_data(
        session.session_id,
        stream.stream_id,
        byte_count=2048,
        frame_count=3,
    )

    assert stream.frame_count == 3
    assert stream.byte_count == 2048
    assert stream.last_data_at is not None


def test_stream_requires_active_session() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Pasif")

    with pytest.raises(
        RuntimeSessionError,
        match="aktif olmalıdır",
    ):
        manager.attach_stream(
            session.session_id,
            stream_type=RuntimeStreamType.VIDEO,
            source="telefon",
        )


def test_pause_deactivates_streams() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Akış")
    manager.start(session.session_id)

    stream = manager.attach_stream(
        session.session_id,
        stream_type=RuntimeStreamType.SENSOR,
        source="prob",
    )

    manager.pause(session.session_id)

    assert stream.active is False


def test_link_evidence_to_stream() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Kanıt")
    manager.start(session.session_id)

    stream = manager.attach_stream(
        session.session_id,
        stream_type=RuntimeStreamType.PHOTO,
        source="kamera",
        stream_id="FOTO-1",
    )

    link = manager.link_evidence(
        session.session_id,
        evidence_id="KANIT-1",
        evidence_type="fotoğraf",
        source_stream_id=stream.stream_id,
    )

    assert link.evidence_id == "KANIT-1"
    assert len(session.evidence_links) == 1


def test_duplicate_evidence_is_rejected() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Kanıt")

    manager.link_evidence(
        session.session_id,
        evidence_id="KANIT-1",
        evidence_type="fotoğraf",
    )

    with pytest.raises(
        RuntimeSessionError,
        match="zaten oturuma bağlı",
    ):
        manager.link_evidence(
            session.session_id,
            evidence_id="KANIT-1",
            evidence_type="fotoğraf",
        )


def test_dynamic_map_pin_is_created() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Harita")

    pin = manager.add_map_pin(
        session.session_id,
        pin_id="PIN-1",
        pin_type="araştırma_noktası",
        label="Keban kıyı noktası",
        confidence=0.94,
        location=RuntimeLocation(
            latitude=38.8001,
            longitude=38.7402,
            altitude_m=845.0,
            accuracy_m=0.02,
            source="RTK",
        ),
    )

    assert pin.pin_id == "PIN-1"
    assert pin.location.source == "RTK"
    assert pin.confidence == 0.94
    assert len(session.map_pins) == 1


def test_invalid_location_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Enlem",
    ):
        RuntimeLocation(
            latitude=120.0,
            longitude=30.0,
        )


def test_timeout_closes_inactive_session() -> None:
    manager, clock = create_manager()

    session = manager.create_session(
        name="Zaman aşımı",
        timeout=timedelta(minutes=5),
    )

    manager.start(session.session_id)

    clock.advance(timedelta(minutes=6))

    expired = manager.expire_timed_out_sessions()

    assert expired == (session,)
    assert session.state is (
        RuntimeSessionState.TIMED_OUT
    )
    assert manager.snapshot()[
        "aktif_oturum_kimliği"
    ] is None


def test_recent_activity_prevents_timeout() -> None:
    manager, clock = create_manager()

    session = manager.create_session(
        name="Hareketli",
        timeout=timedelta(minutes=5),
    )

    manager.start(session.session_id)

    stream = manager.attach_stream(
        session.session_id,
        stream_type=RuntimeStreamType.SENSOR,
        source="sensör",
    )

    clock.advance(timedelta(minutes=4))

    manager.record_stream_data(
        session.session_id,
        stream.stream_id,
        byte_count=128,
    )

    clock.advance(timedelta(minutes=4))

    assert manager.expire_timed_out_sessions() == tuple()
    assert session.state is RuntimeSessionState.ACTIVE


def test_stop_completes_session_safely() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Kapanış")
    manager.start(session.session_id)

    stream = manager.attach_stream(
        session.session_id,
        stream_type=RuntimeStreamType.VIDEO,
        source="drone",
    )

    manager.stop(session.session_id)

    assert session.state is (
        RuntimeSessionState.COMPLETED
    )
    assert session.stopped_at is not None
    assert stream.active is False


def test_fail_marks_session_and_reason() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Hatalı")
    manager.start(session.session_id)

    manager.fail(
        session.session_id,
        reason="kamera bağlantısı kesildi",
    )

    assert session.state is RuntimeSessionState.FAILED
    assert session.failure_reason == (
        "kamera bağlantısı kesildi"
    )


def test_snapshot_preserves_turkish_keys() -> None:
    manager, _ = create_manager()

    session = manager.create_session(
        name="Türkçe oturum",
        metadata={
            "açıklama": "yüzey ve bitki analizi",
        },
    )

    manager.start(session.session_id)

    payload = manager.snapshot()
    session_payload = payload["oturumlar"][0]

    assert payload["toplam_oturum_sayısı"] == 1
    assert payload["aktif_oturum_sayısı"] == 1
    assert session_payload["durum"] == "aktif"
    assert session_payload["veri"]["açıklama"] == (
        "yüzey ve bitki analizi"
    )


def test_session_events_are_published() -> None:
    manager, _ = create_manager()

    session = manager.create_session(name="Olay")
    manager.start(session.session_id)

    stream = manager.attach_stream(
        session.session_id,
        stream_type=RuntimeStreamType.CAMERA,
        source="kamera",
    )

    manager.record_stream_data(
        session.session_id,
        stream.stream_id,
        byte_count=512,
    )

    manager.add_map_pin(
        session.session_id,
        location=RuntimeLocation(
            latitude=39.0,
            longitude=38.0,
        ),
        pin_type="gözlem",
        label="Gözlem noktası",
    )

    manager.stop(session.session_id)

    topics = [
        event.topic
        for event in manager.event_bus.history
    ]

    assert "runtime.session.created" in topics
    assert "runtime.session.started" in topics
    assert (
        "runtime.session.stream.attached"
        in topics
    )
    assert (
        "runtime.session.stream.data"
        in topics
    )
    assert (
        "runtime.session.map_pin.created"
        in topics
    )
    assert (
        "runtime.session.completed"
        in topics
    )
