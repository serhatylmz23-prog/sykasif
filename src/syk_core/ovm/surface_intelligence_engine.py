"""Dinamik Yüzey Zekâsı görselleştirme ve analiz motoru."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean
from typing import Any

from .annotation import (
    AnnotationRecord,
    AnnotationShape,
    AnnotationStyle,
)
from .entity import OvmEntity
from .enums import (
    EntityKind,
    RuntimeState,
    VisualStatus,
)
from .surface_models import (
    SurfaceFeature,
    SurfaceFeatureKind,
    SurfaceInput,
    SurfaceProcessingStage,
    SurfaceSeverity,
)


_FEATURE_ENTITY_KIND: dict[
    SurfaceFeatureKind,
    EntityKind,
] = {
    SurfaceFeatureKind.CAVITY: EntityKind.CAVITY,
    SurfaceFeatureKind.CHANNEL: EntityKind.CHANNEL,
    SurfaceFeatureKind.CRACK: EntityKind.CRACK,
    SurfaceFeatureKind.MINERAL_VEIN: (
        EntityKind.MINERAL_VEIN
    ),
    SurfaceFeatureKind.SURFACE_EROSION: (
        EntityKind.SURFACE_EROSION
    ),
    SurfaceFeatureKind.ROUGHNESS: EntityKind.ROUGHNESS,
    SurfaceFeatureKind.SLOPE: EntityKind.SLOPE,
    SurfaceFeatureKind.DEPRESSION: EntityKind.CAVITY,
    SurfaceFeatureKind.PROTRUSION: (
        EntityKind.SURFACE_MODEL
    ),
    SurfaceFeatureKind.EDGE: EntityKind.SURFACE_MODEL,
    SurfaceFeatureKind.COLOR_ANOMALY: (
        EntityKind.SPECTRAL
    ),
    SurfaceFeatureKind.THERMAL_ANOMALY: (
        EntityKind.THERMAL
    ),
    SurfaceFeatureKind.SPECTRAL_ANOMALY: (
        EntityKind.SPECTRAL
    ),
    SurfaceFeatureKind.UNKNOWN: EntityKind.AI_ANALYSIS,
}


_FEATURE_TURKISH_LABELS: dict[
    SurfaceFeatureKind,
    str,
] = {
    SurfaceFeatureKind.CAVITY: "Oyuk / Boşluk",
    SurfaceFeatureKind.CHANNEL: "Kanal",
    SurfaceFeatureKind.CRACK: "Çatlak",
    SurfaceFeatureKind.MINERAL_VEIN: "Mineral Damarı",
    SurfaceFeatureKind.SURFACE_EROSION: "Yüzey Aşınımı",
    SurfaceFeatureKind.ROUGHNESS: "Pürüzlülük",
    SurfaceFeatureKind.SLOPE: "Eğim",
    SurfaceFeatureKind.DEPRESSION: "Çöküntü",
    SurfaceFeatureKind.PROTRUSION: "Çıkıntı",
    SurfaceFeatureKind.EDGE: "Kenar",
    SurfaceFeatureKind.COLOR_ANOMALY: "Renk Anomalisi",
    SurfaceFeatureKind.THERMAL_ANOMALY: "Termal Anomali",
    SurfaceFeatureKind.SPECTRAL_ANOMALY: "Spektral Anomali",
    SurfaceFeatureKind.UNKNOWN: "Bilinmeyen Yüzey Özelliği",
}


@dataclass(slots=True)
class SurfaceStageResult:
    """DTSE işlem aşaması sonucu."""

    stage: SurfaceProcessingStage
    progress_percent: float
    completed: bool
    message: str
    output_entity_ids: tuple[str, ...] = tuple()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.progress_percent = float(
            self.progress_percent
        )

        if not 0.0 <= self.progress_percent <= 100.0:
            raise ValueError(
                "İşlem ilerlemesi 0 ile 100 arasında olmalıdır."
            )

        self.message = self.message.strip()

        if not self.message:
            raise ValueError(
                "İşlem aşaması açıklaması boş olamaz."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "aşama": self.stage.value,
            "ilerleme_yüzdesi": self.progress_percent,
            "tamamlandı": self.completed,
            "açıklama": self.message,
            "çıktı_varlıkları": list(
                self.output_entity_ids
            ),
            "üst_veri": self.metadata,
        }


@dataclass(slots=True)
class SurfaceAnalysisResult:
    """Tek yüzey zekâsı çalışmasının birleşik sonucu."""

    analysis_id: str
    inputs: tuple[SurfaceInput, ...]
    features: tuple[SurfaceFeature, ...]
    entities: tuple[OvmEntity, ...]
    annotations: tuple[AnnotationRecord, ...]
    stages: tuple[SurfaceStageResult, ...]
    overall_confidence: float
    review_required: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "analiz_kimliği": self.analysis_id,
            "girdi_sayısı": len(self.inputs),
            "tespit_sayısı": len(self.features),
            "varlık_sayısı": len(self.entities),
            "işaret_sayısı": len(self.annotations),
            "genel_güven": self.overall_confidence,
            "inceleme_gerekli": self.review_required,
            "işlem_aşamaları": [
                stage.to_dict()
                for stage in self.stages
            ],
            "tespitler": [
                feature.to_dict()
                for feature in self.features
            ],
            "üst_veri": self.metadata,
        }


class SurfaceIntelligenceEngine:
    """DTSE yüzey tespitlerini OVM ve SyFrame kayıtlarına dönüştürür."""

    def analyze(
        self,
        *,
        analysis_id: str,
        inputs: tuple[SurfaceInput, ...],
        features: tuple[SurfaceFeature, ...],
        source_research_point_id: str | None = None,
    ) -> SurfaceAnalysisResult:
        if not analysis_id.strip():
            raise ValueError(
                "Yüzey analizi kimliği boş olamaz."
            )

        if not inputs:
            raise ValueError(
                "Yüzey analizi için en az bir girdi gereklidir."
            )

        entities: list[OvmEntity] = []
        annotations: list[AnnotationRecord] = []

        for feature in features:
            entity = self._create_entity(
                feature=feature,
                analysis_id=analysis_id,
                source_research_point_id=(
                    source_research_point_id
                ),
            )

            annotation = self._create_annotation(
                feature=feature,
                entity=entity,
            )

            entities.append(entity)
            annotations.append(annotation)

        stages = self._create_stage_results(
            inputs=inputs,
            entities=tuple(entities),
        )

        overall_confidence = (
            round(
                fmean(
                    feature.confidence_score
                    for feature in features
                ),
                3,
            )
            if features
            else 0.0
        )

        review_required = any(
            feature.requires_review
            for feature in features
        )

        return SurfaceAnalysisResult(
            analysis_id=analysis_id.strip(),
            inputs=inputs,
            features=features,
            entities=tuple(entities),
            annotations=tuple(annotations),
            stages=stages,
            overall_confidence=overall_confidence,
            review_required=review_required,
            metadata={
                "source_research_point_id": (
                    source_research_point_id
                ),
                "dynamic": True,
                "engine": "SYK-DTSE",
                "engine_version": "0.1",
            },
        )

    def _create_entity(
        self,
        *,
        feature: SurfaceFeature,
        analysis_id: str,
        source_research_point_id: str | None,
    ) -> OvmEntity:
        visual_status = self._resolve_visual_status(
            feature
        )

        runtime_state = (
            RuntimeState.VERIFYING
            if feature.requires_review
            else RuntimeState.COMPLETED
        )

        label = _FEATURE_TURKISH_LABELS[
            feature.kind
        ]

        entity = OvmEntity(
            kind=_FEATURE_ENTITY_KIND[feature.kind],
            title=feature.title or label,
            description=feature.description,
            parent_id=source_research_point_id,
            layer_code=(
                f"dtse.{feature.kind.value}"
            ),
            runtime_state=runtime_state,
            visual_status=visual_status,
            confidence_score=feature.confidence_score,
            icon_code=(
                f"syk-dtse-{feature.kind.value.replace('_', '-')}"
            ),
            metadata={
                "analysis_id": analysis_id,
                "feature_id": feature.feature_id,
                "feature_kind": feature.kind.value,
                "severity": feature.severity.value,
                "region": feature.region.to_dict(),
                "measurements": [
                    measurement.to_dict()
                    for measurement
                    in feature.measurements
                ],
                "depth_m": feature.depth_m,
                "width_m": feature.width_m,
                "length_m": feature.length_m,
                "area_m2": feature.area_m2,
                "volume_m3": feature.volume_m3,
                "evidence_ids": sorted(
                    feature.evidence_ids
                ),
                "source_entity_ids": sorted(
                    feature.source_entity_ids
                ),
                "dynamic": True,
            },
        )

        entity.set_dynamic_style(
            pulse=(
                visual_status
                in {
                    VisualStatus.ANALYZING,
                    VisualStatus.RARE_ANOMALY,
                    VisualStatus.CRITICAL,
                }
            ),
            confidence=feature.confidence_score,
            severity=feature.severity.value,
            frame_shape="corner_frame",
            label=label,
        )

        return entity

    def _create_annotation(
        self,
        *,
        feature: SurfaceFeature,
        entity: OvmEntity,
    ) -> AnnotationRecord:
        visual_status = self._resolve_visual_status(
            feature
        )

        description_parts: list[str] = []

        if feature.description:
            description_parts.append(
                feature.description
            )

        description_parts.append(
            f"Güven: %{feature.confidence_score:.1f}"
        )

        if feature.depth_m is not None:
            description_parts.append(
                f"Derinlik: {feature.depth_m:.3f} m"
            )

        if feature.width_m is not None:
            description_parts.append(
                f"Genişlik: {feature.width_m:.3f} m"
            )

        if feature.length_m is not None:
            description_parts.append(
                f"Uzunluk: {feature.length_m:.3f} m"
            )

        annotation = AnnotationRecord(
            title=feature.title,
            description=" · ".join(
                description_parts
            ),
            shape=AnnotationShape.RECTANGLE,
            points=feature.region.to_points(),
            style=AnnotationStyle.from_status(
                visual_status
            ),
            target_entity_id=entity.entity_id,
            evidence_ids=set(feature.evidence_ids),
            metadata={
                "feature_id": feature.feature_id,
                "feature_kind": feature.kind.value,
                "severity": feature.severity.value,
                "dynamic": True,
                "auto_generated": True,
                "source": "SYK-DTSE",
            },
        )

        return annotation

    @staticmethod
    def _resolve_visual_status(
        feature: SurfaceFeature,
    ) -> VisualStatus:
        if feature.severity == SurfaceSeverity.CRITICAL:
            return VisualStatus.CRITICAL

        if feature.severity == SurfaceSeverity.HIGH:
            return VisualStatus.REVIEW_REQUIRED

        if feature.confidence_score < 40.0:
            return VisualStatus.LOW_CONFIDENCE

        if feature.kind in {
            SurfaceFeatureKind.THERMAL_ANOMALY,
            SurfaceFeatureKind.SPECTRAL_ANOMALY,
            SurfaceFeatureKind.COLOR_ANOMALY,
        } and feature.confidence_score >= 80.0:
            return VisualStatus.RARE_ANOMALY

        if feature.confidence_score >= 99.9:
            return VisualStatus.VERIFIED

        if feature.confidence_score >= 80.0:
            return VisualStatus.ANALYZING

        return VisualStatus.REVIEW_REQUIRED

    @staticmethod
    def _create_stage_results(
        *,
        inputs: tuple[SurfaceInput, ...],
        entities: tuple[OvmEntity, ...],
    ) -> tuple[SurfaceStageResult, ...]:
        point_cloud_available = any(
            item.kind.value == "point_cloud"
            for item in inputs
        )
        mesh_available = any(
            item.kind.value == "adaptive_mesh"
            for item in inputs
        )

        entity_ids = tuple(
            entity.entity_id
            for entity in entities
        )

        return (
            SurfaceStageResult(
                stage=SurfaceProcessingStage.PERCEPTION,
                progress_percent=100.0,
                completed=True,
                message="Kaynak yüzey verileri algılandı.",
            ),
            SurfaceStageResult(
                stage=SurfaceProcessingStage.POINT_CLOUD,
                progress_percent=(
                    100.0
                    if point_cloud_available
                    else 0.0
                ),
                completed=point_cloud_available,
                message=(
                    "Nokta bulutu işlendi."
                    if point_cloud_available
                    else "Nokta bulutu girdisi bulunmadı."
                ),
            ),
            SurfaceStageResult(
                stage=SurfaceProcessingStage.ADAPTIVE_MESH,
                progress_percent=(
                    100.0
                    if mesh_available
                    else 0.0
                ),
                completed=mesh_available,
                message=(
                    "Adaptif ağ işlendi."
                    if mesh_available
                    else "Adaptif ağ girdisi bulunmadı."
                ),
            ),
            SurfaceStageResult(
                stage=SurfaceProcessingStage.SURFACE_MODEL,
                progress_percent=100.0,
                completed=True,
                message="Yüzey özellikleri ortak modele dönüştürüldü.",
            ),
            SurfaceStageResult(
                stage=SurfaceProcessingStage.COLORIZATION,
                progress_percent=100.0,
                completed=True,
                message="Dinamik durum stilleri üretildi.",
            ),
            SurfaceStageResult(
                stage=SurfaceProcessingStage.ANALYSIS_LAYERS,
                progress_percent=100.0,
                completed=True,
                message="Analiz katmanları ve SyFrame işaretleri üretildi.",
                output_entity_ids=entity_ids,
            ),
            SurfaceStageResult(
                stage=SurfaceProcessingStage.RESULT_REPORT,
                progress_percent=100.0,
                completed=True,
                message="Yüzey zekâsı sonucu rapor motoruna hazırlandı.",
                output_entity_ids=entity_ids,
            ),
        )
