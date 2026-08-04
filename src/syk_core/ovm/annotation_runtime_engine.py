"""SyFrame dinamik açıklama ve işaretleme çalışma motoru."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .annotation import (
    AnnotationAnchor,
    AnnotationRecord,
    AnnotationShape,
    AnnotationStyle,
)
from .enums import VisualStatus
from .surface_models import (
    BoundingRegion,
    SurfaceFeature,
    SurfaceFeatureKind,
)


@dataclass(slots=True, frozen=True)
class FrameRenderInstruction:
    """Arayüzün çizeceği dinamik SyFrame talimatı."""

    annotation_id: str
    target_entity_id: str | None
    shape: AnnotationShape
    points: tuple[tuple[float, float], ...]
    anchor: AnnotationAnchor
    stroke_width: float
    opacity: float
    pulse: bool
    dashed: bool
    glow_strength: float
    visual_status: VisualStatus
    label: str
    description: str | None
    icon_code: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "işaret_kimliği": self.annotation_id,
            "hedef_varlık": self.target_entity_id,
            "geometri": self.shape.value,
            "noktalar": [
                {
                    "x": x,
                    "y": y,
                }
                for x, y in self.points
            ],
            "bağlantı": self.anchor.value,
            "çizgi_kalınlığı": self.stroke_width,
            "opaklık": self.opacity,
            "nabız": self.pulse,
            "kesikli": self.dashed,
            "ışıma": self.glow_strength,
            "durum": self.visual_status.value,
            "etiket": self.label,
            "açıklama": self.description,
            "ikon": self.icon_code,
            "üst_veri": self.metadata,
        }


class AnnotationRuntimeEngine:
    """SyFrame kayıtlarını arayüz çizim talimatlarına dönüştürür."""

    _STATUS_ICON_CODES: dict[
        VisualStatus,
        str,
    ] = {
        VisualStatus.NEUTRAL: "syk-frame-neutral",
        VisualStatus.VERIFIED: "syk-frame-verified",
        VisualStatus.ANALYZING: "syk-frame-analyzing",
        VisualStatus.REVIEW_REQUIRED: (
            "syk-frame-review-required"
        ),
        VisualStatus.LOW_CONFIDENCE: (
            "syk-frame-low-confidence"
        ),
        VisualStatus.INCONSISTENT: (
            "syk-frame-inconsistent"
        ),
        VisualStatus.RARE_ANOMALY: (
            "syk-frame-rare-anomaly"
        ),
        VisualStatus.REFERENCE: "syk-frame-reference",
        VisualStatus.CRITICAL: "syk-frame-critical",
    }

    def render_instruction(
        self,
        *,
        annotation_id: str,
        annotation: AnnotationRecord,
    ) -> FrameRenderInstruction:
        if not annotation_id.strip():
            raise ValueError(
                "SyFrame işaret kimliği boş olamaz."
            )

        return FrameRenderInstruction(
            annotation_id=annotation_id.strip(),
            target_entity_id=(
                annotation.target_entity_id
            ),
            shape=annotation.shape,
            points=annotation.points,
            anchor=annotation.anchor,
            stroke_width=(
                annotation.style.stroke_width
            ),
            opacity=annotation.style.opacity,
            pulse=annotation.style.pulse,
            dashed=annotation.style.dashed,
            glow_strength=(
                annotation.style.glow_strength
            ),
            visual_status=annotation.style.status,
            label=annotation.title,
            description=annotation.description,
            icon_code=self._STATUS_ICON_CODES[
                annotation.style.status
            ],
            metadata={
                **annotation.metadata,
                "evidence_ids": sorted(
                    annotation.evidence_ids
                ),
                "dynamic": True,
            },
        )

    def render_many(
        self,
        annotations: tuple[
            tuple[str, AnnotationRecord],
            ...,
        ],
    ) -> tuple[FrameRenderInstruction, ...]:
        instructions = [
            self.render_instruction(
                annotation_id=annotation_id,
                annotation=annotation,
            )
            for annotation_id, annotation
            in annotations
        ]

        instructions.sort(
            key=lambda item: (
                self._status_priority(
                    item.visual_status
                ),
                item.label,
            )
        )

        return tuple(instructions)

    @staticmethod
    def _status_priority(
        status: VisualStatus,
    ) -> int:
        priorities = {
            VisualStatus.CRITICAL: 0,
            VisualStatus.INCONSISTENT: 1,
            VisualStatus.RARE_ANOMALY: 2,
            VisualStatus.REVIEW_REQUIRED: 3,
            VisualStatus.LOW_CONFIDENCE: 4,
            VisualStatus.ANALYZING: 5,
            VisualStatus.VERIFIED: 6,
            VisualStatus.REFERENCE: 7,
            VisualStatus.NEUTRAL: 8,
        }

        return priorities[status]

    def create_manual_annotation(
        self,
        *,
        title: str,
        region: BoundingRegion,
        status: VisualStatus,
        description: str | None = None,
        target_entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AnnotationRecord:
        return AnnotationRecord(
            title=title,
            description=description,
            shape=AnnotationShape.RECTANGLE,
            points=region.to_points(),
            anchor=AnnotationAnchor.AUTO,
            style=AnnotationStyle.from_status(
                status
            ),
            target_entity_id=target_entity_id,
            metadata={
                **(metadata or {}),
                "dynamic": True,
                "auto_generated": False,
                "source": "SyFrame",
            },
        )

    def create_feature_annotation(
        self,
        *,
        feature: SurfaceFeature,
        target_entity_id: str | None = None,
    ) -> AnnotationRecord:
        status = self._feature_status(feature)

        return AnnotationRecord(
            title=feature.title,
            description=feature.description,
            shape=AnnotationShape.RECTANGLE,
            points=feature.region.to_points(),
            anchor=AnnotationAnchor.AUTO,
            style=AnnotationStyle.from_status(
                status
            ),
            target_entity_id=target_entity_id,
            evidence_ids=set(feature.evidence_ids),
            metadata={
                "feature_id": feature.feature_id,
                "feature_kind": feature.kind.value,
                "dynamic": True,
                "auto_generated": True,
                "source": "SYK-DTSE",
            },
        )

    @staticmethod
    def _feature_status(
        feature: SurfaceFeature,
    ) -> VisualStatus:
        if feature.confidence_score >= 99.9:
            return VisualStatus.VERIFIED

        if feature.confidence_score < 40:
            return VisualStatus.LOW_CONFIDENCE

        if feature.kind in {
            SurfaceFeatureKind.THERMAL_ANOMALY,
            SurfaceFeatureKind.SPECTRAL_ANOMALY,
            SurfaceFeatureKind.COLOR_ANOMALY,
        }:
            return VisualStatus.RARE_ANOMALY

        if feature.requires_review:
            return VisualStatus.REVIEW_REQUIRED

        return VisualStatus.ANALYZING
