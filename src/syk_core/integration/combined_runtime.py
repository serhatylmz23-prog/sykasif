"""Ortak Varlık Modeli birleşik kapanış çalışma motoru."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import fmean
from typing import Any
from uuid import uuid4

from ..ecosystem import (
    EcosystemAnalysisResult,
    EcosystemRuntimeContext,
    EcosystemRuntimeEngine,
    FishSpeciesProfile,
    PlantSpeciesProfile,
)
from ..integrity import calculate_payload_sha256
from ..live_analysis import (
    AnalysisFrame,
    DynamicMapPin,
    LiveAnalysisResult,
    LiveAnalysisSession,
    LiveDetection,
)
from ..live_persistence import (
    LiveAnalysisManifest,
    LiveAnalysisRepository,
    LiveReportBridge,
    LiveReportPayload,
)
from ..ovm import (
    AnnotationRecord,
    AnnotationRuntimeEngine,
    FrameRenderInstruction,
    OvmEntity,
    SurfaceAnalysisResult,
    SurfaceFeature,
    SurfaceInput,
    SurfaceIntelligenceEngine,
)
from ..utils import json_safe, utc_now


@dataclass(slots=True, frozen=True)
class CombinedRuntimeRequest:
    """Birleşik çalışma motoruna giren doğrulanabilir veri."""

    context: EcosystemRuntimeContext
    frame: AnalysisFrame
    detections: tuple[LiveDetection, ...]

    fish_profiles: tuple[
        FishSpeciesProfile,
        ...,
    ] = tuple()

    plant_profiles: tuple[
        PlantSpeciesProfile,
        ...,
    ] = tuple()

    surface_inputs: tuple[
        SurfaceInput,
        ...,
    ] = tuple()

    surface_features: tuple[
        SurfaceFeature,
        ...,
    ] = tuple()

    actor: str = "system"
    cluster_distance_m: float = 20.0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValueError(
                "Birleşik çalışma aktörü boş olamaz."
            )

        if self.cluster_distance_m <= 0:
            raise ValueError(
                "Küme mesafesi sıfırdan büyük olmalıdır."
            )

        if (
            self.frame.location.latitude
            != self.context.location.latitude
            or self.frame.location.longitude
            != self.context.location.longitude
        ):
            object.__setattr__(
                self,
                "metadata",
                {
                    **self.metadata,
                    "konum_farkı": True,
                },
            )


@dataclass(slots=True, frozen=True)
class CombinedRuntimeSummary:
    """Birleşik çalışma sonucunun kısa özeti."""

    session_id: str
    live_detection_count: int
    fish_match_count: int
    plant_match_count: int
    surface_feature_count: int
    annotation_count: int
    frame_instruction_count: int
    map_pin_count: int
    ovm_entity_count: int
    evidence_reference_count: int
    review_required: bool
    average_confidence: float
    generated_at: Any = field(
        default_factory=utc_now
    )

    def to_runtime_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "oturum_kimliği": self.session_id,
                "canlı_tespit_sayısı": (
                    self.live_detection_count
                ),
                "balık_eşleşme_sayısı": (
                    self.fish_match_count
                ),
                "bitki_eşleşme_sayısı": (
                    self.plant_match_count
                ),
                "yüzey_tespiti_sayısı": (
                    self.surface_feature_count
                ),
                "işaret_sayısı": (
                    self.annotation_count
                ),
                "çerçeve_talimatı_sayısı": (
                    self.frame_instruction_count
                ),
                "harita_pini_sayısı": (
                    self.map_pin_count
                ),
                "ortak_varlık_sayısı": (
                    self.ovm_entity_count
                ),
                "kanıt_referansı_sayısı": (
                    self.evidence_reference_count
                ),
                "inceleme_gerekli": (
                    self.review_required
                ),
                "ortalama_güven": (
                    self.average_confidence
                ),
                "üretilme_zamanı": (
                    self.generated_at
                ),
            }
        )


@dataclass(slots=True)
class CombinedRuntimeResult:
    """GPS → kamera → analiz → harita → kanıt → rapor sonucu."""

    run_id: str
    session: LiveAnalysisSession
    live_result: LiveAnalysisResult
    ecosystem_result: EcosystemAnalysisResult
    surface_result: SurfaceAnalysisResult | None
    annotations: tuple[
        AnnotationRecord,
        ...,
    ]
    frame_instructions: tuple[
        FrameRenderInstruction,
        ...,
    ]
    map_pins: tuple[
        DynamicMapPin,
        ...,
    ]
    ovm_entities: tuple[
        OvmEntity,
        ...,
    ]
    manifest: LiveAnalysisManifest
    report_payload: LiveReportPayload
    summary: CombinedRuntimeSummary
    repository_root: str
    run_sha256: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        calculated = self.calculate_hash()

        if self.run_sha256 is None:
            self.run_sha256 = calculated
        elif self.run_sha256 != calculated:
            raise ValueError(
                "Birleşik çalışma SHA-256 değeri geçersiz."
            )

    def unsigned_payload(self) -> dict[str, Any]:
        return json_safe(
            {
                "run_id": self.run_id,
                "session_id": (
                    self.session.session_id
                ),
                "summary": (
                    self.summary.to_runtime_dict()
                ),
                "manifest_sha256": (
                    self.manifest.manifest_sha256
                ),
                "report_sha256": (
                    self.report_payload.payload_sha256
                ),
                "map_pin_ids": [
                    pin.pin_id
                    for pin in self.map_pins
                ],
                "ovm_entity_ids": [
                    entity.entity_id
                    for entity in self.ovm_entities
                ],
                "repository_root": (
                    self.repository_root
                ),
                "metadata": self.metadata,
            }
        )

    def calculate_hash(self) -> str:
        return calculate_payload_sha256(
            self.unsigned_payload()
        )

    def verify(self) -> bool:
        return (
            self.run_sha256
            == self.calculate_hash()
            and self.manifest.verify()
            and self.report_payload.verify()
        )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            **self.unsigned_payload(),
            "run_sha256": self.run_sha256,
            "canlı_analiz": (
                self.live_result.to_runtime_dict()
            ),
            "ekosistem": (
                self.ecosystem_result
                .to_runtime_dict()
            ),
            "yüzey_zekâsı": (
                self.surface_result
                .to_runtime_dict()
                if self.surface_result
                is not None
                else None
            ),
            "çerçeve_talimatları": [
                instruction.to_runtime_dict()
                for instruction
                in self.frame_instructions
            ],
            "harita_pinleri": [
                pin.to_runtime_dict()
                for pin in self.map_pins
            ],
            "ortak_varlıklar": [
                entity.to_runtime_dict()
                for entity in self.ovm_entities
            ],
            "manifest": (
                self.manifest.to_dict()
            ),
            "rapor_verisi": (
                self.report_payload.to_dict()
            ),
        }


class CombinedRuntimeEngine:
    """SyKaşif Ortak Varlık Modeli birleşik çalışma motoru."""

    def __init__(
        self,
        *,
        repository_root: str | Path,
    ) -> None:
        self.repository = (
            LiveAnalysisRepository(
                repository_root
            )
        )
        self.ecosystem_engine = (
            EcosystemRuntimeEngine()
        )
        self.surface_engine = (
            SurfaceIntelligenceEngine()
        )
        self.annotation_engine = (
            AnnotationRuntimeEngine()
        )
        self.report_bridge = (
            LiveReportBridge()
        )

    def execute(
        self,
        request: CombinedRuntimeRequest,
    ) -> CombinedRuntimeResult:
        run_id = (
            "SYK-OVM-RUN-"
            + uuid4().hex[:16].upper()
        )

        session = LiveAnalysisSession(
            context=request.context,
            session_id=(
                "SYK-LIVE-"
                + uuid4().hex[:16].upper()
            ),
        )
        session.start()
        session.enqueue_frame(
            request.frame
        )

        live_result = session.process_next(
            detections=request.detections
        )

        ecosystem_result = (
            self.ecosystem_engine.analyze(
                context=request.context,
                fish_profiles=(
                    request.fish_profiles
                ),
                plant_profiles=(
                    request.plant_profiles
                ),
                fish_observations=(
                    live_result
                    .fish_observations
                ),
                plant_observations=(
                    live_result
                    .plant_observations
                ),
            )
        )

        surface_result = (
            self._run_surface_analysis(
                run_id=run_id,
                request=request,
            )
        )

        annotations = self._merge_annotations(
            live_result=live_result,
            surface_result=surface_result,
        )

        frame_instructions = (
            self._create_frame_instructions(
                annotations
            )
        )

        map_pins = (
            session.create_cluster_pins(
                maximum_distance_m=(
                    request.cluster_distance_m
                )
            )
        )

        manifest = (
            self.repository.save_session(
                session,
                actor=request.actor,
            )
        )

        self.repository.save_pin_history(
            session_id=session.session_id,
            pins=map_pins,
        )

        manifest = (
            self.repository.load_manifest(
                session.session_id
            )
        )

        report_payload = (
            self.report_bridge.build(
                session=session,
                manifest=manifest,
                pins=tuple(
                    pin.to_runtime_dict()
                    for pin in map_pins
                ),
            )
        )

        ovm_entities = (
            self._merge_entities(
                ecosystem_result=(
                    ecosystem_result
                ),
                surface_result=(
                    surface_result
                ),
            )
        )

        summary = self._create_summary(
            session=session,
            live_result=live_result,
            ecosystem_result=(
                ecosystem_result
            ),
            surface_result=surface_result,
            annotations=annotations,
            frame_instructions=(
                frame_instructions
            ),
            map_pins=map_pins,
            ovm_entities=ovm_entities,
            report_payload=(
                report_payload
            ),
        )

        result = CombinedRuntimeResult(
            run_id=run_id,
            session=session,
            live_result=live_result,
            ecosystem_result=(
                ecosystem_result
            ),
            surface_result=surface_result,
            annotations=annotations,
            frame_instructions=(
                frame_instructions
            ),
            map_pins=map_pins,
            ovm_entities=ovm_entities,
            manifest=manifest,
            report_payload=report_payload,
            summary=summary,
            repository_root=str(
                self.repository
                .root_directory
            ),
            metadata={
                **request.metadata,
                "dynamic": True,
                "pipeline": [
                    "GPS",
                    "Kamera",
                    "Canlı Tespit",
                    "DTSE",
                    "SyFrame",
                    "Ekosistem",
                    "Harita Pini",
                    "Kanıt",
                    "Manifest",
                    "Rapor",
                ],
            },
        )

        if not self.repository.verify(
            session.session_id
        ):
            raise ValueError(
                "Birleşik çalışma kayıt doğrulaması başarısız."
            )

        if not result.verify():
            raise ValueError(
                "Birleşik çalışma sonuç doğrulaması başarısız."
            )

        return result

    def restore_session(
        self,
        session_id: str,
    ) -> LiveAnalysisSession:
        return (
            self.repository.restore_session(
                session_id
            )
        )

    def _run_surface_analysis(
        self,
        *,
        run_id: str,
        request: CombinedRuntimeRequest,
    ) -> SurfaceAnalysisResult | None:
        if (
            not request.surface_inputs
            and not request.surface_features
        ):
            return None

        if not request.surface_inputs:
            raise ValueError(
                "Yüzey özellikleri için en az bir yüzey girdisi gereklidir."
            )

        return self.surface_engine.analyze(
            analysis_id=(
                f"{run_id}-DTSE"
            ),
            inputs=request.surface_inputs,
            features=request.surface_features,
            source_research_point_id=(
                request.metadata.get(
                    "research_point_id"
                )
            ),
        )

    @staticmethod
    def _merge_annotations(
        *,
        live_result: LiveAnalysisResult,
        surface_result: (
            SurfaceAnalysisResult | None
        ),
    ) -> tuple[AnnotationRecord, ...]:
        annotations = list(
            live_result.annotations
        )

        if surface_result is not None:
            annotations.extend(
                surface_result.annotations
            )

        return tuple(annotations)

    def _create_frame_instructions(
        self,
        annotations: tuple[
            AnnotationRecord,
            ...,
        ],
    ) -> tuple[
        FrameRenderInstruction,
        ...,
    ]:
        indexed = tuple(
            (
                f"SYK-FRAME-{index:04d}",
                annotation,
            )
            for index, annotation
            in enumerate(
                annotations,
                start=1,
            )
        )

        return (
            self.annotation_engine
            .render_many(indexed)
        )

    @staticmethod
    def _merge_entities(
        *,
        ecosystem_result: (
            EcosystemAnalysisResult
        ),
        surface_result: (
            SurfaceAnalysisResult | None
        ),
    ) -> tuple[OvmEntity, ...]:
        entities = list(
            ecosystem_result.entities
        )

        if surface_result is not None:
            entities.extend(
                surface_result.entities
            )

        entity_ids: set[str] = set()
        unique_entities: list[
            OvmEntity
        ] = []

        for entity in entities:
            if entity.entity_id in entity_ids:
                continue

            entity_ids.add(
                entity.entity_id
            )
            unique_entities.append(
                entity
            )

        return tuple(
            sorted(
                unique_entities,
                key=lambda item: (
                    item.layer_order,
                    item.title,
                ),
            )
        )

    @staticmethod
    def _create_summary(
        *,
        session: LiveAnalysisSession,
        live_result: LiveAnalysisResult,
        ecosystem_result: (
            EcosystemAnalysisResult
        ),
        surface_result: (
            SurfaceAnalysisResult | None
        ),
        annotations: tuple[
            AnnotationRecord,
            ...,
        ],
        frame_instructions: tuple[
            FrameRenderInstruction,
            ...,
        ],
        map_pins: tuple[
            DynamicMapPin,
            ...,
        ],
        ovm_entities: tuple[
            OvmEntity,
            ...,
        ],
        report_payload: LiveReportPayload,
    ) -> CombinedRuntimeSummary:
        confidence_values: list[
            float
        ] = [
            detection.confidence_score
            for detection
            in live_result.detections
        ]

        confidence_values.extend(
            match.score
            for match
            in ecosystem_result
            .fish_result
            .matches
        )

        confidence_values.extend(
            match.score
            for match
            in ecosystem_result
            .plant_result
            .matches
        )

        if surface_result is not None:
            confidence_values.extend(
                feature.confidence_score
                for feature
                in surface_result.features
            )

        average_confidence = (
            round(
                fmean(
                    confidence_values
                ),
                3,
            )
            if confidence_values
            else 0.0
        )

        review_required = any(
            entity.confidence_score
            is not None
            and entity.confidence_score
            < 80.0
            for entity in ovm_entities
        )

        if (
            surface_result is not None
            and surface_result
            .review_required
        ):
            review_required = True

        evidence_reference_count = len(
            report_payload
            .evidence_blocks
        )

        return CombinedRuntimeSummary(
            session_id=session.session_id,
            live_detection_count=len(
                live_result.detections
            ),
            fish_match_count=len(
                ecosystem_result
                .fish_result
                .matches
            ),
            plant_match_count=len(
                ecosystem_result
                .plant_result
                .matches
            ),
            surface_feature_count=(
                len(
                    surface_result.features
                )
                if surface_result
                is not None
                else 0
            ),
            annotation_count=len(
                annotations
            ),
            frame_instruction_count=len(
                frame_instructions
            ),
            map_pin_count=len(
                map_pins
            ),
            ovm_entity_count=len(
                ovm_entities
            ),
            evidence_reference_count=(
                evidence_reference_count
            ),
            review_required=(
                review_required
            ),
            average_confidence=(
                average_confidence
            ),
        )
