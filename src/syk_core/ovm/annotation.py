"""SyFrame dinamik çerçeve ve açıklama modeli."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .enums import VisualStatus
from .localization import ensure_utf8_text


class AnnotationShape(StrEnum):
    """İşaretleme geometrisi."""

    POINT = "point"
    RECTANGLE = "rectangle"
    POLYGON = "polygon"
    CIRCLE = "circle"
    ARROW = "arrow"
    LINE = "line"
    FREEHAND = "freehand"


class AnnotationAnchor(StrEnum):
    """Açıklama kutusunun bağlantı konumu."""

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    AUTO = "auto"


@dataclass(slots=True)
class AnnotationStyle:
    """SyFrame durumuna göre dinamik çizim stili."""

    stroke_width: float = 2.0
    opacity: float = 1.0
    corner_length: float = 24.0
    pulse: bool = False
    dashed: bool = False
    glow_strength: float = 0.0
    status: VisualStatus = VisualStatus.NEUTRAL

    def __post_init__(self) -> None:
        if self.stroke_width <= 0:
            raise ValueError(
                "Çizgi kalınlığı sıfırdan büyük olmalıdır."
            )

        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError(
                "Açıklama opaklığı 0.0 ile 1.0 arasında olmalıdır."
            )

        if self.corner_length < 0:
            raise ValueError(
                "Köşe uzunluğu negatif olamaz."
            )

        if not 0.0 <= self.glow_strength <= 1.0:
            raise ValueError(
                "Işıma değeri 0.0 ile 1.0 arasında olmalıdır."
            )

    @classmethod
    def from_status(
        cls,
        status: VisualStatus,
    ) -> "AnnotationStyle":
        mapping: dict[
            VisualStatus,
            dict[str, Any],
        ] = {
            VisualStatus.NEUTRAL: {
                "opacity": 0.72,
                "pulse": False,
                "dashed": False,
                "glow_strength": 0.12,
            },
            VisualStatus.VERIFIED: {
                "opacity": 1.0,
                "pulse": False,
                "dashed": False,
                "glow_strength": 0.35,
            },
            VisualStatus.ANALYZING: {
                "opacity": 0.92,
                "pulse": True,
                "dashed": True,
                "glow_strength": 0.45,
            },
            VisualStatus.REVIEW_REQUIRED: {
                "opacity": 0.92,
                "pulse": True,
                "dashed": False,
                "glow_strength": 0.40,
            },
            VisualStatus.LOW_CONFIDENCE: {
                "opacity": 0.78,
                "pulse": False,
                "dashed": True,
                "glow_strength": 0.20,
            },
            VisualStatus.INCONSISTENT: {
                "opacity": 1.0,
                "pulse": True,
                "dashed": False,
                "glow_strength": 0.55,
            },
            VisualStatus.RARE_ANOMALY: {
                "opacity": 1.0,
                "pulse": True,
                "dashed": False,
                "glow_strength": 0.65,
            },
            VisualStatus.REFERENCE: {
                "opacity": 0.82,
                "pulse": False,
                "dashed": True,
                "glow_strength": 0.18,
            },
            VisualStatus.CRITICAL: {
                "opacity": 1.0,
                "pulse": True,
                "dashed": False,
                "glow_strength": 0.80,
            },
        }

        return cls(
            status=status,
            **mapping[status],
        )


@dataclass(slots=True)
class AnnotationRecord:
    """Görsel üzerine bırakılan dinamik açıklama."""

    title: str
    shape: AnnotationShape
    points: tuple[tuple[float, float], ...]
    description: str | None = None
    anchor: AnnotationAnchor = AnnotationAnchor.AUTO
    style: AnnotationStyle = field(
        default_factory=AnnotationStyle
    )
    target_entity_id: str | None = None
    evidence_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.title = ensure_utf8_text(self.title)

        if self.description is not None:
            self.description = ensure_utf8_text(
                self.description
            )

        minimum_points = {
            AnnotationShape.POINT: 1,
            AnnotationShape.RECTANGLE: 2,
            AnnotationShape.POLYGON: 3,
            AnnotationShape.CIRCLE: 2,
            AnnotationShape.ARROW: 2,
            AnnotationShape.LINE: 2,
            AnnotationShape.FREEHAND: 2,
        }

        if len(self.points) < minimum_points[self.shape]:
            raise ValueError(
                f"{self.shape.value} için yetersiz koordinat."
            )

        for x, y in self.points:
            if not 0.0 <= float(x) <= 1.0:
                raise ValueError(
                    "X koordinatı 0.0 ile 1.0 arasında olmalıdır."
                )

            if not 0.0 <= float(y) <= 1.0:
                raise ValueError(
                    "Y koordinatı 0.0 ile 1.0 arasında olmalıdır."
                )

    def add_evidence(
        self,
        evidence_id: str,
    ) -> None:
        self.evidence_ids.add(
            ensure_utf8_text(evidence_id)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "shape": self.shape.value,
            "points": [
                {
                    "x": x,
                    "y": y,
                }
                for x, y in self.points
            ],
            "anchor": self.anchor.value,
            "style": {
                "stroke_width": self.style.stroke_width,
                "opacity": self.style.opacity,
                "corner_length": self.style.corner_length,
                "pulse": self.style.pulse,
                "dashed": self.style.dashed,
                "glow_strength": self.style.glow_strength,
                "status": self.style.status.value,
            },
            "target_entity_id": self.target_entity_id,
            "evidence_ids": sorted(self.evidence_ids),
            "metadata": self.metadata,
        }
