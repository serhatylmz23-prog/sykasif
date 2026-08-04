from __future__ import annotations

from datetime import UTC, datetime

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
    DetectionState,
    FrameProcessingState,
    FrameQueue,
    FrameQueueEmptyError,
    FrameQueueFullError,
    GeoClusterEngine,
    LiveAnalysisSession,
    LiveDetection,
    LiveSessionState,
    MapPinState,
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
        water_body_type=WaterBodyType.RESERVOIR,
        water_body_name="Keban Baraj Gölü",
        device_data_available=True,
    )


def create_frame(
    *,
    latitude: float = 38.806,
    longitude: float = 38.744,
    sequence: int = 1,
) -> AnalysisFrame:
    return AnalysisFrame(
        source=ObservationSource.LIVE_CAMERA,
        location=GeoLocation(
            latitude=latitude,
            longitude=longitude,
        ),
        width_px=1920,
        height_px=1080,
        sequence_number=sequence,
    )


def create_detection(
    *,
    entity_type: str,
    label: str,
    confidence: float,
    species_id: str,
    condition: PlantCondition = PlantCondition.UNKNOWN,
) -> LiveDetection:
    return LiveDetection(
        entity_type=entity_type,
        label=label,
        confidence_score=confidence,
        species_id=species_id,
        track_id=f"TRACK-{species_id}",
        condition=condition,
        region=BoundingRegion(
            top_left=NormalizedPoint(
                x=0.15,
                y=0.20,
            ),
            bottom_right=NormalizedPoint(
                x=0.55,
                y=0.75,
            ),
        ),
    )


def test_frame_queue_flow() -> None:
    queue = FrameQueue(
        capacity=2
    )

    first = create_frame(
        sequence=1
    )
    second = create_frame(
        sequence=2
    )

    queue.enqueue(first)
    queue.enqueue(second)

    assert len(queue) == 2
    assert first.frame_id in queue

    with pytest.raises(
        FrameQueueFullError
    ):
        queue.enqueue(
            create_frame(sequence=3)
        )

    selected = queue.dequeue()

    assert selected is first
    assert (
        selected.state
        == FrameProcessingState.PROCESSING
    )
    assert len(queue) == 1


def test_empty_queue_raises_error() -> None:
    queue = FrameQueue()

    with pytest.raises(
        FrameQueueEmptyError
    ):
        queue.dequeue()


def test_live_session_processes_fish_and_plant() -> None:
    session = LiveAnalysisSession(
        context=create_context()
    )
    session.start()

    frame = create_frame()
    session.enqueue_frame(frame)

    result = session.process_next(
        detections=(
            create_detection(
                entity_type="fish",
                label="Sazan",
                confidence=91.0,
                species_id="sazan",
            ),
            create_detection(
                entity_type="plant",
                label="Söğüt",
                confidence=88.0,
                species_id="sogut",
                condition=PlantCondition.HEALTHY,
            ),
        )
    )

    assert session.state == LiveSessionState.ACTIVE
    assert session.processed_frame_count == 1
    assert len(result.history_records) == 2
    assert len(result.annotations) == 2
    assert len(result.map_pins) == 2
    assert len(result.fish_observations) == 1
    assert len(result.plant_observations) == 1
    assert (
        result.frame.state
        == FrameProcessingState.ANALYZED
    )


def test_live_detection_creates_dynamic_pin() -> None:
    session = LiveAnalysisSession(
        context=create_context()
    )
    session.start()
    session.enqueue_frame(
        create_frame()
    )

    result = session.process_next(
        detections=(
            create_detection(
                entity_type="plant",
                label="Kamış",
                confidence=72.0,
                species_id="kamis",
            ),
        )
    )

    pin = result.map_pins[0]

    assert pin.state == MapPinState.ACTIVE
    assert pin.layer_code == "ecosystem.plant"
    assert pin.icon_code.startswith(
        "syk-live-plant-"
    )
    assert pin.dynamic_style["count_badge"] is False


def test_low_confidence_detection_requires_review() -> None:
    session = LiveAnalysisSession(
        context=create_context()
    )
    session.start()
    session.enqueue_frame(
        create_frame()
    )

    result = session.process_next(
        detections=(
            create_detection(
                entity_type="plant",
                label="Bilinmeyen Bitki",
                confidence=54.0,
                species_id="unknown",
            ),
        )
    )

    record = result.history_records[0]
    pin = result.map_pins[0]

    assert (
        record.state
        == DetectionState.REVIEW_REQUIRED
    )
    assert (
        pin.state
        == MapPinState.REVIEW_REQUIRED
    )
    assert pin.dynamic_style["pulse"] is True


def test_session_pause_and_stop() -> None:
    session = LiveAnalysisSession(
        context=create_context()
    )

    session.start()
    assert session.state == LiveSessionState.ACTIVE

    session.pause()
    assert session.state == LiveSessionState.PAUSED

    session.stop()
    assert session.state == LiveSessionState.STOPPED


def test_geo_cluster_groups_nearby_records() -> None:
    session = LiveAnalysisSession(
        context=create_context()
    )
    session.start()

    session.enqueue_frame(
        create_frame(
            latitude=38.806000,
            longitude=38.744000,
            sequence=1,
        )
    )
    session.process_next(
        detections=(
            create_detection(
                entity_type="plant",
                label="Söğüt",
                confidence=88.0,
                species_id="sogut",
            ),
        )
    )

    session.enqueue_frame(
        create_frame(
            latitude=38.806020,
            longitude=38.744020,
            sequence=2,
        )
    )
    session.process_next(
        detections=(
            create_detection(
                entity_type="plant",
                label="Kamış",
                confidence=82.0,
                species_id="kamis",
            ),
        )
    )

    clusters = session.clusters(
        maximum_distance_m=10.0
    )

    assert len(clusters) == 1
    assert clusters[0].observation_count == 2

    pins = session.create_cluster_pins(
        maximum_distance_m=10.0
    )

    assert len(pins) == 1
    assert (
        pins[0].state
        == MapPinState.CLUSTERED
    )
    assert pins[0].count == 2
    assert (
        pins[0].dynamic_style[
            "count_badge"
        ]
        is True
    )


def test_geo_cluster_separates_distant_records() -> None:
    session = LiveAnalysisSession(
        context=create_context()
    )
    session.start()

    session.enqueue_frame(
        create_frame(
            latitude=38.806,
            longitude=38.744,
            sequence=1,
        )
    )
    session.process_next(
        detections=(
            create_detection(
                entity_type="fish",
                label="Sazan",
                confidence=90.0,
                species_id="sazan",
            ),
        )
    )

    session.enqueue_frame(
        create_frame(
            latitude=38.816,
            longitude=38.754,
            sequence=2,
        )
    )
    session.process_next(
        detections=(
            create_detection(
                entity_type="fish",
                label="Yayın",
                confidence=84.0,
                species_id="yayin",
            ),
        )
    )

    clusters = GeoClusterEngine().cluster(
        session.history.all(),
        maximum_distance_m=30.0,
    )

    assert len(clusters) == 2


def test_runtime_payload_preserves_turkish() -> None:
    session = LiveAnalysisSession(
        context=create_context()
    )
    session.start()
    session.enqueue_frame(
        create_frame()
    )

    result = session.process_next(
        detections=(
            create_detection(
                entity_type="plant",
                label="Söğüt",
                confidence=88.0,
                species_id="sogut",
                condition=PlantCondition.HEALTHY,
            ),
        )
    )

    payload = result.to_runtime_dict()

    assert payload["tespit_sayısı"] == 1
    assert payload["bitki_gözlemi_sayısı"] == 1
    assert payload["harita_pinleri"][0]["başlık"] == "Söğüt"
