"""Dinamik yüzey zekâsı veri modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from typing import Any

from .localization import ensure_utf8_text


class SurfaceFeatureKind(StrEnum):
    """Yüzey üzerinde tespit edilen özellik türleri."""

    CAVITY = "cavity"
    CHANNEL = "channel"
    CRACK = "crack"
    MINERAL_VEIN = "mineral_vein"
    SURFACE_EROSION = "surface_erosion"
    ROUGHNESS = "roughness"
    SLOPE = "slope"
    DEPRESSION = "depression"
    PROTRUSION = "protrusion"
    EDGE = "edge"
    COLOR_ANOMALY = "color_anomaly"
    THERMAL_ANOMALY = "thermal_anomaly"
    SPECTRAL_ANOMALY = "spectral_anomaly"
    UNKNOWN = "unknown"


class SurfaceInputKind(StrEnum):
    """Yüzey zekâsına giren veri türleri."""

    PHOTO = "photo"
    VIDEO_FRAME = "video_frame"
    POINT_CLOUD = "point_cloud"
    ADAPTIVE_MESH = "adaptive_mesh"
    THREE_D_MODEL = "three_d_model"
    LIDAR = "lidar"
    THERMAL = "thermal"
    SPECTRAL = "spectral"
    DEPTH_MAP = "depth_map"
    MANUAL = "manual"


class SurfaceSeverity(StrEnum):
    """Tespitin önem seviyesi."""

    INFORMATION = "information"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SurfaceProcessingStage(StrEnum):
    """DTSE işlem aşamaları."""

    PERCEPTION = "perception"
    POINT_CLOUD = "point_cloud"
    ADAPTIVE_MESH = "adaptive_mesh"
    SURFACE_MODEL = "surface_model"
    COLORIZATION = "colorization"
    ANALYSIS_LAYERS = "analysis_layers"
    RESULT_REPORT = "result_report"


@dataclass(slots=True, frozen=True)
class NormalizedPoint:
    """0.0–1.0 aralığında ekran veya görüntü koordinatı."""

    x: float
    y: float

    def __post_init__(self) -> None:
        x = float(self.x)
        y = float(self.y)

        if not isfinite(x) or not isfinite(y):
            raise ValueError(
                "Yüzey koordinatları sonlu sayı olmalıdır."
            )

        if not 0.0 <= x <= 1.0:
            raise ValueError(
                "X koordinatı 0.0 ile 1.0 arasında olmalıdır."
            )

        if not 0.0 <= y <= 1.0:
            raise ValueError(
                "Y koordinatı 0.0 ile 1.0 arasında olmalıdır."
            )

        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
        }


@dataclass(slots=True, frozen=True)
class BoundingRegion:
    """Tespitin görüntü üzerindeki sınır alanı."""

    top_left: NormalizedPoint
    bottom_right: NormalizedPoint

    def __post_init__(self) -> None:
        if self.top_left.x >= self.bottom_right.x:
            raise ValueError(
                "Sınır alanında sol değer sağ değerden küçük olmalıdır."
            )

        if self.top_left.y >= self.bottom_right.y:
            raise ValueError(
                "Sınır alanında üst değer alt değerden küçük olmalıdır."
            )

    @property
    def width(self) -> float:
        return self.bottom_right.x - self.top_left.x

    @property
    def height(self) -> float:
        return self.bottom_right.y - self.top_left.y

    @property
    def area_ratio(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> NormalizedPoint:
        return NormalizedPoint(
            x=(
                self.top_left.x
                + self.bottom_right.x
            ) / 2,
            y=(
                self.top_left.y
                + self.bottom_right.y
            ) / 2,
        )

    def to_points(
        self,
    ) -> tuple[tuple[float, float], ...]:
        return (
            (
                self.top_left.x,
                self.top_left.y,
            ),
            (
                self.bottom_right.x,
                self.bottom_right.y,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sol_üst": self.top_left.to_dict(),
            "sağ_alt": self.bottom_right.to_dict(),
            "genişlik": self.width,
            "yükseklik": self.height,
            "alan_oranı": self.area_ratio,
            "merkez": self.center.to_dict(),
        }


@dataclass(slots=True)
class SurfaceMeasurement:
    """Tek bir yüzey ölçüm değeri."""

    name: str
    value: float
    unit: str
    minimum: float | None = None
    maximum: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = ensure_utf8_text(self.name)
        self.unit = ensure_utf8_text(self.unit)
        self.value = float(self.value)

        if not isfinite(self.value):
            raise ValueError(
                "Ölçüm değeri sonlu sayı olmalıdır."
            )

        if self.minimum is not None:
            self.minimum = float(self.minimum)

        if self.maximum is not None:
            self.maximum = float(self.maximum)

        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError(
                "Ölçüm alt sınırı üst sınırdan büyük olamaz."
            )

    @property
    def within_limits(self) -> bool | None:
        if (
            self.minimum is None
            and self.maximum is None
        ):
            return None

        if (
            self.minimum is not None
            and self.value < self.minimum
        ):
            return False

        if (
            self.maximum is not None
            and self.value > self.maximum
        ):
            return False

        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ad": self.name,
            "değer": self.value,
            "birim": self.unit,
            "alt_sınır": self.minimum,
            "üst_sınır": self.maximum,
            "sınırlar_içinde": self.within_limits,
            "üst_veri": self.metadata,
        }


@dataclass(slots=True)
class SurfaceFeature:
    """Yüzey zekâsının ürettiği doğrulanabilir özellik kaydı."""

    feature_id: str
    kind: SurfaceFeatureKind
    title: str
    region: BoundingRegion
    confidence_score: float
    severity: SurfaceSeverity = SurfaceSeverity.INFORMATION
    description: str | None = None
    depth_m: float | None = None
    width_m: float | None = None
    length_m: float | None = None
    area_m2: float | None = None
    volume_m3: float | None = None
    measurements: list[SurfaceMeasurement] = field(
        default_factory=list
    )
    evidence_ids: set[str] = field(default_factory=set)
    source_entity_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.feature_id = ensure_utf8_text(
            self.feature_id
        )
        self.title = ensure_utf8_text(self.title)

        if self.description is not None:
            self.description = ensure_utf8_text(
                self.description
            )

        self.confidence_score = float(
            self.confidence_score
        )

        if not 0.0 <= self.confidence_score <= 100.0:
            raise ValueError(
                "Yüzey özelliği güven skoru 0 ile 100 arasında olmalıdır."
            )

        for field_name in (
            "depth_m",
            "width_m",
            "length_m",
            "area_m2",
            "volume_m3",
        ):
            value = getattr(self, field_name)

            if value is not None:
                normalized = float(value)

                if normalized < 0:
                    raise ValueError(
                        f"{field_name} negatif olamaz."
                    )

                setattr(
                    self,
                    field_name,
                    normalized,
                )

    def add_measurement(
        self,
        measurement: SurfaceMeasurement,
    ) -> None:
        self.measurements.append(measurement)

    def add_evidence(
        self,
        evidence_id: str,
    ) -> None:
        self.evidence_ids.add(
            ensure_utf8_text(evidence_id)
        )

    def add_source(
        self,
        entity_id: str,
    ) -> None:
        self.source_entity_ids.add(
            ensure_utf8_text(entity_id)
        )

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence_score >= 80.0

    @property
    def requires_review(self) -> bool:
        return (
            self.confidence_score < 60.0
            or self.severity
            in {
                SurfaceSeverity.HIGH,
                SurfaceSeverity.CRITICAL,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "özellik_kimliği": self.feature_id,
            "tür": self.kind.value,
            "başlık": self.title,
            "açıklama": self.description,
            "güven_skoru": self.confidence_score,
            "önem": self.severity.value,
            "derinlik_m": self.depth_m,
            "genişlik_m": self.width_m,
            "uzunluk_m": self.length_m,
            "alan_m2": self.area_m2,
            "hacim_m3": self.volume_m3,
            "sınır": self.region.to_dict(),
            "ölçümler": [
                measurement.to_dict()
                for measurement in self.measurements
            ],
            "kanıt_kimlikleri": sorted(
                self.evidence_ids
            ),
            "kaynak_varlıklar": sorted(
                self.source_entity_ids
            ),
            "yüksek_güven": self.is_high_confidence,
            "inceleme_gerekli": self.requires_review,
            "üst_veri": self.metadata,
        }


@dataclass(slots=True)
class SurfaceInput:
    """DTSE motoruna giren kaynak veri."""

    input_id: str
    kind: SurfaceInputKind
    source_uri: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    point_count: int | None = None
    vertex_count: int | None = None
    coordinate_system: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.input_id = ensure_utf8_text(
            self.input_id
        )

        for name in (
            "width_px",
            "height_px",
            "point_count",
            "vertex_count",
        ):
            value = getattr(self, name)

            if value is not None:
                normalized = int(value)

                if normalized < 0:
                    raise ValueError(
                        f"{name} negatif olamaz."
                    )

                setattr(
                    self,
                    name,
                    normalized,
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "girdi_kimliği": self.input_id,
            "girdi_türü": self.kind.value,
            "kaynak": self.source_uri,
            "genişlik_px": self.width_px,
            "yükseklik_px": self.height_px,
            "nokta_sayısı": self.point_count,
            "köşe_sayısı": self.vertex_count,
            "koordinat_sistemi": self.coordinate_system,
            "üst_veri": self.metadata,
        }
