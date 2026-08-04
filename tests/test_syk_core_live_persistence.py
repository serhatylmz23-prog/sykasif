from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from syk_core import GeoLocation
from syk_core.ecosystem import (
    EcosystemRuntimeContext,
    ObservationSource,
    PlantCondition,
    SalinityType,
    WaterBodyType,
)
from syk_core.live_analysis import (
    AnalysisFrame,
    LiveAnalysisSession,
    LiveDetection,
    LiveSessionState,
)
from syk_core.live_persistence import (
    LiveAnalysisIntegrityError,
    LiveAnalysisRepository,
    LiveReportBridge,
)
from syk_core.ovm import (
    BoundingRegion,
    NormalizedPoint,
)


def create_context() -> EcosystemRuntimeContext:
    return EcosystemRuntimeContext(
        location=GeoLocation(
            latitude=38.806,
            longitude=38.744,
            altitude_m=845.0,
        ),
        region_code="TR-ELAZIG-KEBAN",
        region_name="Keban",
        observed_at=datetime(
            2026,
            8,
            4,
            17,
            30,
            tzinfo=UTC,
        ),
        salinity=SalinityType.FRESHWATER,
        water_body_type=(
            WaterBodyType.RESERVOIR
        ),
        water_body_name=(
            "Keban Baraj Gölü"
        ),
        device_data_available=True,
    )


def create_session() -> LiveAnalysisSession:
    session = LiveAnalysisSession(
        context=create_context(),
        session_id=(
            "SYK-LIVE-PERSISTENCE-001"
        ),
    )
    session.start()

    frame = AnalysisFrame(
        source=(
            ObservationSource.LIVE_CAMERA
        ),
        location=GeoLocation(
            latitude=38.806,
            longitude=38.744,
        ),
        width_px=1920,
        height_px=1080,
        sequence_number=1,
    )

    session.enqueue_frame(frame)

    region = BoundingRegion(
        top_left=NormalizedPoint(
            x=0.15,
            y=0.20,
        ),
        bottom_right=NormalizedPoint(
            x=0.55,
            y=0.75,
        ),
    )

    session.process_next(
        detections=(
            LiveDetection(
                entity_type="fish",
                label="Sazan",
                confidence_score=91.0,
                region=region,
                species_id="sazan",
                evidence_ids={
                    "SYK-EVD-FISH-001",
                },
            ),
            LiveDetection(
                entity_type="plant",
                label="Söğüt",
                confidence_score=88.0,
                region=region,
                species_id="sogut",
                condition=(
                    PlantCondition.HEALTHY
                ),
                evidence_ids={
                    "SYK-EVD-PLANT-001",
                },
            ),
        )
    )

    return session


def test_live_repository_save_load_verify(
    tmp_path: Path,
) -> None:
    repository = LiveAnalysisRepository(
        tmp_path / "live_repository"
    )
    session = create_session()

    manifest = repository.save_session(
        session,
        actor="Bilge Kaan",
    )

    snapshot = repository.load_snapshot(
        session.session_id
    )

    assert (
        snapshot.session_id
        == session.session_id
    )
    assert (
        snapshot.processed_frame_count
        == 1
    )
    assert len(
        snapshot.history_records
    ) == 2
    assert manifest.verify() is True
    assert (
        repository.verify(
            session.session_id
        )
        is True
    )


def test_live_session_restore_is_safe(
    tmp_path: Path,
) -> None:
    repository = LiveAnalysisRepository(
        tmp_path / "live_repository"
    )
    session = create_session()

    repository.save_session(session)

    restored = repository.restore_session(
        session.session_id
    )

    assert (
        restored.session_id
        == session.session_id
    )
    assert (
        restored.state
        == LiveSessionState.PAUSED
    )
    assert (
        restored.processed_frame_count
        == 1
    )
    assert len(restored.history) == 2
    assert (
        restored.metadata[
            "restored_from_snapshot"
        ]
        is True
    )


def test_second_save_extends_audit_chain(
    tmp_path: Path,
) -> None:
    repository = LiveAnalysisRepository(
        tmp_path / "live_repository"
    )
    session = create_session()

    repository.save_session(
        session,
        actor="Kurucu Kaan",
    )

    session.metadata[
        "revision"
    ] = 2

    repository.save_session(
        session,
        actor="Kurucu Kaan",
    )

    chain = repository.load_audit_chain(
        session.session_id
    )

    assert len(chain.events) == 2
    assert (
        chain.events[1].previous_hash
        == chain.events[0].event_sha256
    )
    assert chain.verify() is True


def test_snapshot_tampering_is_detected(
    tmp_path: Path,
) -> None:
    repository = LiveAnalysisRepository(
        tmp_path / "live_repository"
    )
    session = create_session()

    repository.save_session(session)

    path = (
        repository.snapshot_directory
        / (
            f"{session.session_id}"
            ".snapshot.json"
        )
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )
    payload["payload"][
        "processed_frame_count"
    ] = 999

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        LiveAnalysisIntegrityError
    ):
        repository.load_snapshot(
            session.session_id
        )


def test_pin_history_roundtrip(
    tmp_path: Path,
) -> None:
    repository = LiveAnalysisRepository(
        tmp_path / "live_repository"
    )
    session = create_session()

    repository.save_session(session)

    pins = session.create_cluster_pins(
        maximum_distance_m=20.0
    )

    digest = repository.save_pin_history(
        session_id=session.session_id,
        pins=pins,
    )

    loaded = repository.load_pin_history(
        session.session_id
    )

    assert len(digest) == 64
    assert len(loaded) == 1
    assert loaded[0]["sayı"] == 2
    assert (
        repository.verify(
            session.session_id
        )
        is True
    )


def test_report_bridge_creates_dynamic_blocks(
    tmp_path: Path,
) -> None:
    repository = LiveAnalysisRepository(
        tmp_path / "live_repository"
    )
    session = create_session()

    manifest = repository.save_session(
        session
    )

    pins = tuple(
        pin.to_runtime_dict()
        for pin in (
            session.create_cluster_pins(
                maximum_distance_m=20.0
            )
        )
    )

    payload = LiveReportBridge().build(
        session=session,
        manifest=manifest,
        pins=pins,
    )

    assert payload.verify() is True
    assert (
        payload.summary[
            "detection_count"
        ]
        == 2
    )
    assert (
        payload.summary[
            "fish_detection_count"
        ]
        == 1
    )
    assert (
        payload.summary[
            "plant_detection_count"
        ]
        == 1
    )
    assert len(
        payload.map_blocks
    ) == 1
    assert len(
        payload.detection_blocks
    ) == 2
    assert len(
        payload.evidence_blocks
    ) == 2


def test_repository_list_and_delete(
    tmp_path: Path,
) -> None:
    repository = LiveAnalysisRepository(
        tmp_path / "live_repository"
    )
    session = create_session()

    repository.save_session(session)

    assert (
        session.session_id
        in repository.list_session_ids()
    )

    repository.delete_session(
        session.session_id
    )

    assert (
        session.session_id
        not in repository.list_session_ids()
    )
