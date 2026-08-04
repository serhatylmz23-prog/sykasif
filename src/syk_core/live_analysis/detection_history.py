"""Canlı bitki ve canlı tespit geçmişi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..location import GeoLocation
from ..utils import json_safe, utc_now
from .enums import DetectionState


@dataclass(slots=True)
class DetectionHistoryRecord:
    """Tek canlı tespit geçmişi kaydı."""

    entity_type: str
    detected_label: str
    confidence_score: float
    location: GeoLocation
    frame_id: str
    record_id: str = field(
        default_factory=lambda: (
            f"SYK-DET-{uuid4().hex[:16].upper()}"
        )
    )
    detected_at: datetime = field(default_factory=utc_now)
    state: DetectionState = DetectionState.NEW
    track_id: str | None = None
    species_id: str | None = None
    evidence_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.entity_type = self.entity_type.strip()
        self.detected_label = self.detected_label.strip()
        self.frame_id = self.frame_id.strip()

        if not self.entity_type:
            raise ValueError(
                "Tespit varlık türü boş olamaz."
            )

        if not self.detected_label:
            raise ValueError(
                "Tespit etiketi boş olamaz."
            )

        if not self.frame_id:
            raise ValueError(
                "Tespit kare kimliği boş olamaz."
            )

        self.confidence_score = float(
            self.confidence_score
        )

        if not 0.0 <= self.confidence_score <= 100.0:
            raise ValueError(
                "Tespit güven skoru 0 ile 100 arasında olmalıdır."
            )

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "record_id": self.record_id,
                "entity_type": self.entity_type,
                "detected_label": self.detected_label,
                "confidence_score": self.confidence_score,
                "location": self.location.to_dict(),
                "frame_id": self.frame_id,
                "detected_at": self.detected_at,
                "state": self.state,
                "track_id": self.track_id,
                "species_id": self.species_id,
                "evidence_ids": sorted(self.evidence_ids),
                "metadata": self.metadata,
            }
        )


class DetectionHistory:
    """Canlı tespit geçmişini yönetir."""

    def __init__(self) -> None:
        self._records: dict[
            str,
            DetectionHistoryRecord,
        ] = {}

    def add(
        self,
        record: DetectionHistoryRecord,
    ) -> None:
        if record.record_id in self._records:
            raise ValueError(
                f"Tespit kaydı zaten mevcut: {record.record_id}"
            )

        self._records[record.record_id] = record

    def get(
        self,
        record_id: str,
    ) -> DetectionHistoryRecord:
        try:
            return self._records[record_id]
        except KeyError as exc:
            raise KeyError(
                f"Tespit kaydı bulunamadı: {record_id}"
            ) from exc

    def by_entity_type(
        self,
        entity_type: str,
    ) -> tuple[DetectionHistoryRecord, ...]:
        normalized = entity_type.strip().casefold()

        return tuple(
            sorted(
                (
                    record
                    for record in self._records.values()
                    if record.entity_type.casefold()
                    == normalized
                ),
                key=lambda item: item.detected_at,
            )
        )

    def by_species(
        self,
        species_id: str,
    ) -> tuple[DetectionHistoryRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._records.values()
                    if record.species_id == species_id
                ),
                key=lambda item: item.detected_at,
            )
        )

    def by_track(
        self,
        track_id: str,
    ) -> tuple[DetectionHistoryRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._records.values()
                    if record.track_id == track_id
                ),
                key=lambda item: item.detected_at,
            )
        )

    def all(
        self,
    ) -> tuple[DetectionHistoryRecord, ...]:
        return tuple(
            sorted(
                self._records.values(),
                key=lambda item: item.detected_at,
            )
        )

    def __len__(self) -> int:
        return len(self._records)
