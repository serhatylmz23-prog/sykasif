"""GPS tabanlı canlı gözlem kümelendirme."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from ..location import GeoLocation
from .detection_history import DetectionHistoryRecord


@dataclass(slots=True)
class GeoCluster:
    """Yakın konumlardaki canlı gözlemlerin kümesi."""

    center: GeoLocation
    cluster_id: str = field(
        default_factory=lambda: (
            f"SYK-CLU-{uuid4().hex[:16].upper()}"
        )
    )
    record_ids: list[str] = field(default_factory=list)
    entity_types: set[str] = field(default_factory=set)
    species_ids: set[str] = field(default_factory=set)
    maximum_radius_m: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def observation_count(self) -> int:
        return len(self.record_ids)

    def add_record(
        self,
        record: DetectionHistoryRecord,
    ) -> None:
        if record.record_id in self.record_ids:
            return

        distance = self.center.distance_to(
            record.location
        )

        self.maximum_radius_m = max(
            self.maximum_radius_m,
            distance,
        )
        self.record_ids.append(record.record_id)
        self.entity_types.add(record.entity_type)

        if record.species_id:
            self.species_ids.add(record.species_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "küme_kimliği": self.cluster_id,
            "merkez": self.center.to_dict(),
            "gözlem_sayısı": self.observation_count,
            "azami_yarıçap_m": self.maximum_radius_m,
            "kayıtlar": list(self.record_ids),
            "varlık_türleri": sorted(self.entity_types),
            "tür_kimlikleri": sorted(self.species_ids),
            "üst_veri": self.metadata,
        }


class GeoClusterEngine:
    """Tespitleri metre tabanlı yakınlıkla kümelendirir."""

    def cluster(
        self,
        records: tuple[
            DetectionHistoryRecord,
            ...,
        ],
        *,
        maximum_distance_m: float = 20.0,
    ) -> tuple[GeoCluster, ...]:
        if maximum_distance_m <= 0:
            raise ValueError(
                "Küme mesafesi sıfırdan büyük olmalıdır."
            )

        clusters: list[GeoCluster] = []

        for record in records:
            target_cluster: GeoCluster | None = None

            for cluster in clusters:
                distance = cluster.center.distance_to(
                    record.location
                )

                if distance <= maximum_distance_m:
                    target_cluster = cluster
                    break

            if target_cluster is None:
                target_cluster = GeoCluster(
                    center=record.location
                )
                clusters.append(target_cluster)

            target_cluster.add_record(record)

        clusters.sort(
            key=lambda item: (
                -item.observation_count,
                item.cluster_id,
            )
        )

        return tuple(clusters)
