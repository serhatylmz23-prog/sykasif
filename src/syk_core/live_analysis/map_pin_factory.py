"""Canlı gözlemden dinamik harita pini üretimi."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from ..location import GeoLocation
from .detection_history import DetectionHistoryRecord
from .enums import MapPinState
from .geo_cluster import GeoCluster


@dataclass(slots=True)
class DynamicMapPin:
    """Canlı analiz sonucundan üretilen harita pini."""

    title: str
    location: GeoLocation
    icon_code: str
    layer_code: str
    pin_id: str = field(
        default_factory=lambda: (
            f"SYK-PIN-{uuid4().hex[:16].upper()}"
        )
    )
    state: MapPinState = MapPinState.NEW
    confidence_score: float | None = None
    count: int = 1
    related_record_ids: tuple[str, ...] = tuple()
    species_ids: tuple[str, ...] = tuple()
    dynamic_style: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.icon_code = self.icon_code.strip()
        self.layer_code = self.layer_code.strip()

        if not self.title:
            raise ValueError(
                "Harita pini başlığı boş olamaz."
            )

        if not self.icon_code:
            raise ValueError(
                "Harita pini ikon kodu boş olamaz."
            )

        if not self.layer_code:
            raise ValueError(
                "Harita pini katman kodu boş olamaz."
            )

        if self.count < 1:
            raise ValueError(
                "Harita pini sayısı en az 1 olmalıdır."
            )

        if self.confidence_score is not None:
            if not 0.0 <= self.confidence_score <= 100.0:
                raise ValueError(
                    "Harita pini güven skoru geçersiz."
                )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "pin_kimliği": self.pin_id,
            "başlık": self.title,
            "konum": self.location.to_dict(),
            "ikon": self.icon_code,
            "katman": self.layer_code,
            "durum": self.state.value,
            "güven_skoru": self.confidence_score,
            "sayı": self.count,
            "kayıtlar": list(self.related_record_ids),
            "türler": list(self.species_ids),
            "dinamik_stil": self.dynamic_style,
            "üst_veri": self.metadata,
        }


class DynamicMapPinFactory:
    """Canlı tespit veya kümeden dinamik pin üretir."""

    def from_record(
        self,
        record: DetectionHistoryRecord,
    ) -> DynamicMapPin:
        species_code = (
            record.species_id
            or record.detected_label
            .casefold()
            .replace(" ", "-")
        )

        layer_code = (
            "ecosystem.fish"
            if record.entity_type.casefold() == "fish"
            else "ecosystem.plant"
            if record.entity_type.casefold() == "plant"
            else "ecosystem.live"
        )

        state = (
            MapPinState.VERIFIED
            if record.confidence_score >= 99.9
            else MapPinState.ACTIVE
            if record.confidence_score >= 70
            else MapPinState.REVIEW_REQUIRED
        )

        return DynamicMapPin(
            title=record.detected_label,
            location=record.location,
            icon_code=(
                f"syk-live-{record.entity_type.casefold()}-"
                f"{species_code}"
            ),
            layer_code=layer_code,
            state=state,
            confidence_score=record.confidence_score,
            related_record_ids=(
                record.record_id,
            ),
            species_ids=(
                (record.species_id,)
                if record.species_id
                else tuple()
            ),
            dynamic_style={
                "pulse": (
                    state
                    == MapPinState.REVIEW_REQUIRED
                ),
                "opacity": (
                    1.0
                    if state == MapPinState.VERIFIED
                    else 0.88
                ),
                "count_badge": False,
            },
            metadata={
                "dynamic": True,
                "source": "live_detection",
            },
        )

    def from_cluster(
        self,
        cluster: GeoCluster,
    ) -> DynamicMapPin:
        entity_label = (
            " / ".join(
                sorted(cluster.entity_types)
            )
            or "Canlı Gözlem"
        )

        return DynamicMapPin(
            title=(
                f"{entity_label} Kümesi "
                f"({cluster.observation_count})"
            ),
            location=cluster.center,
            icon_code="syk-live-cluster",
            layer_code="ecosystem.live.cluster",
            state=MapPinState.CLUSTERED,
            count=cluster.observation_count,
            related_record_ids=tuple(
                cluster.record_ids
            ),
            species_ids=tuple(
                sorted(cluster.species_ids)
            ),
            dynamic_style={
                "pulse": False,
                "opacity": 0.94,
                "count_badge": True,
                "cluster_radius_m": (
                    cluster.maximum_radius_m
                ),
            },
            metadata={
                "dynamic": True,
                "source": "geo_cluster",
                "cluster_id": cluster.cluster_id,
            },
        )
