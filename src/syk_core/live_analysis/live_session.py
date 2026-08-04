"""Canlı kamera analiz oturumu."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import fmean
from typing import Any
from uuid import uuid4

from ..ecosystem import (
    EcosystemRuntimeContext,
    FishObservation,
    ObservationSource,
    PlantCondition,
    PlantObservation,
)
from ..ovm import (
    AnnotationRecord,
    AnnotationRuntimeEngine,
    BoundingRegion,
    NormalizedPoint,
    VisualStatus,
)
from ..utils import json_safe, utc_now
from .detection_history import (
    DetectionHistory,
    DetectionHistoryRecord,
)
from .enums import (
    DetectionState,
    LiveSessionState,
)
from .frame_queue import (
    AnalysisFrame,
    FrameQueue,
)
from .geo_cluster import (
    GeoCluster,
    GeoClusterEngine,
)
from .map_pin_factory import (
    DynamicMapPin,
    DynamicMapPinFactory,
)


@dataclass(slots=True)
class LiveDetection:
    """Tek karede bulunan canlı tespit."""

    entity_type: str
    label: str
    confidence_score: float
    region: BoundingRegion
    detection_id: str = field(
        default_factory=lambda: (
            f"SYK-LDET-{uuid4().hex[:16].upper()}"
        )
    )
    species_id: str | None = None
    track_id: str | None = None
    condition: PlantCondition = PlantCondition.UNKNOWN
    evidence_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.entity_type = self.entity_type.strip()
        self.label = self.label.strip()

        if not self.entity_type:
            raise ValueError(
                "Canlı tespit türü boş olamaz."
            )

        if not self.label:
            raise ValueError(
                "Canlı tespit etiketi boş olamaz."
            )

        self.confidence_score = float(
            self.confidence_score
        )

        if not 0.0 <= self.confidence_score <= 100.0:
            raise ValueError(
                "Canlı tespit güven skoru geçersiz."
            )


@dataclass(slots=True)
class LiveAnalysisResult:
    """Tek kare canlı analiz sonucu."""

    session_id: str
    frame: AnalysisFrame
    detections: tuple[LiveDetection, ...]
    history_records: tuple[
        DetectionHistoryRecord,
        ...,
    ]
    annotations: tuple[
        AnnotationRecord,
        ...,
    ]
    map_pins: tuple[
        DynamicMapPin,
        ...,
    ]
    fish_observations: tuple[
        FishObservation,
        ...,
    ]
    plant_observations: tuple[
        PlantObservation,
        ...,
    ]
    processed_at: datetime = field(default_factory=utc_now)

    @property
    def average_confidence(self) -> float:
        if not self.detections:
            return 0.0

        return round(
            fmean(
                detection.confidence_score
                for detection in self.detections
            ),
            3,
        )

    def to_runtime_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "oturum_kimliği": self.session_id,
                "kare": self.frame.to_dict(),
                "tespit_sayısı": len(self.detections),
                "ortalama_güven": (
                    self.average_confidence
                ),
                "işaretler": [
                    annotation.to_dict()
                    for annotation in self.annotations
                ],
                "harita_pinleri": [
                    pin.to_runtime_dict()
                    for pin in self.map_pins
                ],
                "balık_gözlemi_sayısı": len(
                    self.fish_observations
                ),
                "bitki_gözlemi_sayısı": len(
                    self.plant_observations
                ),
                "işlenme_zamanı": self.processed_at,
            }
        )


class LiveAnalysisSession:
    """Kamera karelerini işleyen dinamik canlı analiz oturumu."""

    def __init__(
        self,
        *,
        context: EcosystemRuntimeContext,
        queue_capacity: int = 120,
        session_id: str | None = None,
    ) -> None:
        self.session_id = (
            session_id
            or (
                f"SYK-LIVE-{uuid4().hex[:16].upper()}"
            )
        )
        self.context = context
        self.state = LiveSessionState.CREATED
        self.created_at = utc_now()
        self.started_at: datetime | None = None
        self.stopped_at: datetime | None = None

        self.frame_queue = FrameQueue(
            capacity=queue_capacity
        )
        self.history = DetectionHistory()
        self.cluster_engine = GeoClusterEngine()
        self.pin_factory = DynamicMapPinFactory()
        self.annotation_engine = AnnotationRuntimeEngine()

        self.processed_frame_count = 0
        self.failed_frame_count = 0
        self.metadata: dict[str, Any] = {}

    def start(self) -> None:
        if self.state not in {
            LiveSessionState.CREATED,
            LiveSessionState.PAUSED,
            LiveSessionState.STOPPED,
        }:
            raise ValueError(
                f"Oturum bu durumdan başlatılamaz: {self.state.value}"
            )

        self.state = LiveSessionState.STARTING
        self.started_at = utc_now()
        self.state = LiveSessionState.ACTIVE

    def pause(self) -> None:
        if self.state != LiveSessionState.ACTIVE:
            raise ValueError(
                "Yalnız aktif oturum duraklatılabilir."
            )

        self.state = LiveSessionState.PAUSED

    def stop(self) -> None:
        if self.state not in {
            LiveSessionState.ACTIVE,
            LiveSessionState.PAUSED,
            LiveSessionState.ERROR,
        }:
            raise ValueError(
                "Oturum bu durumdan durdurulamaz."
            )

        self.state = LiveSessionState.STOPPING
        self.stopped_at = utc_now()
        self.state = LiveSessionState.STOPPED

    def enqueue_frame(
        self,
        frame: AnalysisFrame,
    ) -> None:
        if self.state not in {
            LiveSessionState.ACTIVE,
            LiveSessionState.PAUSED,
        }:
            raise ValueError(
                "Kare eklemek için oturum aktif veya duraklatılmış olmalıdır."
            )

        self.frame_queue.enqueue(frame)

    def process_next(
        self,
        *,
        detections: tuple[
            LiveDetection,
            ...,
        ],
    ) -> LiveAnalysisResult:
        if self.state != LiveSessionState.ACTIVE:
            raise ValueError(
                "Kare işlemek için oturum aktif olmalıdır."
            )

        frame = self.frame_queue.dequeue()

        try:
            result = self._process_frame(
                frame=frame,
                detections=detections,
            )

            frame.mark_analyzed()
            self.processed_frame_count += 1

            return result
        except Exception as exc:
            frame.mark_failed(str(exc))
            self.failed_frame_count += 1
            self.state = LiveSessionState.ERROR
            raise

    def _process_frame(
        self,
        *,
        frame: AnalysisFrame,
        detections: tuple[
            LiveDetection,
            ...,
        ],
    ) -> LiveAnalysisResult:
        history_records: list[
            DetectionHistoryRecord
        ] = []
        annotations: list[AnnotationRecord] = []
        pins: list[DynamicMapPin] = []
        fish_observations: list[
            FishObservation
        ] = []
        plant_observations: list[
            PlantObservation
        ] = []

        for detection in detections:
            state = self._resolve_detection_state(
                detection.confidence_score
            )

            history_record = DetectionHistoryRecord(
                entity_type=detection.entity_type,
                detected_label=detection.label,
                confidence_score=(
                    detection.confidence_score
                ),
                location=frame.location,
                frame_id=frame.frame_id,
                state=state,
                track_id=detection.track_id,
                species_id=detection.species_id,
                evidence_ids=set(
                    detection.evidence_ids
                ),
                metadata={
                    "detection_id": (
                        detection.detection_id
                    ),
                    "region": (
                        detection.region.to_dict()
                    ),
                    "condition": (
                        detection.condition.value
                    ),
                    **detection.metadata,
                },
            )

            self.history.add(history_record)
            history_records.append(history_record)

            annotation = (
                self.annotation_engine
                .create_manual_annotation(
                    title=detection.label,
                    description=(
                        f"{detection.entity_type} · "
                        f"Güven %{detection.confidence_score:.1f}"
                    ),
                    region=detection.region,
                    status=self._resolve_visual_status(
                        detection.confidence_score
                    ),
                    target_entity_id=(
                        history_record.record_id
                    ),
                    metadata={
                        "dynamic": True,
                        "live": True,
                        "frame_id": frame.frame_id,
                        "track_id": detection.track_id,
                        "species_id": (
                            detection.species_id
                        ),
                    },
                )
            )
            annotations.append(annotation)

            pins.append(
                self.pin_factory.from_record(
                    history_record
                )
            )

            normalized_type = (
                detection.entity_type.casefold()
            )

            if normalized_type == "fish":
                fish_observations.append(
                    FishObservation(
                        source=frame.source,
                        detected_label=(
                            detection.label
                        ),
                        model_confidence=(
                            detection.confidence_score
                        ),
                        evidence_ids=set(
                            detection.evidence_ids
                        ),
                        metadata={
                            "frame_id": frame.frame_id,
                            "track_id": detection.track_id,
                            "region": (
                                detection.region.to_dict()
                            ),
                        },
                    )
                )

            if normalized_type == "plant":
                plant_observations.append(
                    PlantObservation(
                        source=frame.source,
                        detected_label=(
                            detection.label
                        ),
                        model_confidence=(
                            detection.confidence_score
                        ),
                        condition=detection.condition,
                        evidence_ids=set(
                            detection.evidence_ids
                        ),
                        metadata={
                            "frame_id": frame.frame_id,
                            "track_id": detection.track_id,
                            "region": (
                                detection.region.to_dict()
                            ),
                        },
                    )
                )

        return LiveAnalysisResult(
            session_id=self.session_id,
            frame=frame,
            detections=detections,
            history_records=tuple(
                history_records
            ),
            annotations=tuple(annotations),
            map_pins=tuple(pins),
            fish_observations=tuple(
                fish_observations
            ),
            plant_observations=tuple(
                plant_observations
            ),
        )

    def create_cluster_pins(
        self,
        *,
        maximum_distance_m: float = 20.0,
    ) -> tuple[DynamicMapPin, ...]:
        clusters = self.cluster_engine.cluster(
            self.history.all(),
            maximum_distance_m=(
                maximum_distance_m
            ),
        )

        return tuple(
            self.pin_factory.from_cluster(cluster)
            for cluster in clusters
        )

    def clusters(
        self,
        *,
        maximum_distance_m: float = 20.0,
    ) -> tuple[GeoCluster, ...]:
        return self.cluster_engine.cluster(
            self.history.all(),
            maximum_distance_m=(
                maximum_distance_m
            ),
        )

    @staticmethod
    def _resolve_detection_state(
        score: float,
    ) -> DetectionState:
        if score >= 99.9:
            return DetectionState.VERIFIED

        if score >= 80:
            return DetectionState.CLASSIFIED

        if score >= 50:
            return DetectionState.REVIEW_REQUIRED

        return DetectionState.NEW

    @staticmethod
    def _resolve_visual_status(
        score: float,
    ) -> VisualStatus:
        if score >= 99.9:
            return VisualStatus.VERIFIED

        if score >= 80:
            return VisualStatus.ANALYZING

        if score >= 50:
            return VisualStatus.REVIEW_REQUIRED

        return VisualStatus.LOW_CONFIDENCE

    def to_runtime_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "oturum_kimliği": self.session_id,
                "durum": self.state,
                "oluşturulma_zamanı": (
                    self.created_at
                ),
                "başlatılma_zamanı": (
                    self.started_at
                ),
                "durdurulma_zamanı": (
                    self.stopped_at
                ),
                "işlenen_kare": (
                    self.processed_frame_count
                ),
                "hatalı_kare": (
                    self.failed_frame_count
                ),
                "kuyruktaki_kare": len(
                    self.frame_queue
                ),
                "tespit_geçmişi": len(
                    self.history
                ),
                "bağlam": self.context.to_dict(),
                "üst_veri": self.metadata,
            }
        )
