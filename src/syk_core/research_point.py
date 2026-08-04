"""Araştırma Noktası ortak varlık modeli."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .constants import RESEARCH_POINT_PREFIX
from .enums import (
    EntityStatus,
    EvidenceStatus,
    LayerCategory,
    ResearchCategory,
)
from .errors import (
    DuplicateEvidenceError,
    InvalidEntityStateError,
)
from .evidence import EvidenceRecord
from .identity import EntityIdentity
from .layer import LayerRecord
from .location import GeoLocation, ResearchArea
from .utils import json_safe, normalize_text


_ALLOWED_STATUS_TRANSITIONS: dict[
    EntityStatus,
    frozenset[EntityStatus],
] = {
    EntityStatus.DRAFT: frozenset(
        {
            EntityStatus.ACTIVE,
            EntityStatus.REJECTED,
            EntityStatus.ARCHIVED,
        }
    ),
    EntityStatus.ACTIVE: frozenset(
        {
            EntityStatus.PROCESSING,
            EntityStatus.WAITING,
            EntityStatus.COMPLETED,
            EntityStatus.REJECTED,
            EntityStatus.ARCHIVED,
        }
    ),
    EntityStatus.PROCESSING: frozenset(
        {
            EntityStatus.ACTIVE,
            EntityStatus.WAITING,
            EntityStatus.COMPLETED,
            EntityStatus.REJECTED,
        }
    ),
    EntityStatus.WAITING: frozenset(
        {
            EntityStatus.ACTIVE,
            EntityStatus.PROCESSING,
            EntityStatus.REJECTED,
            EntityStatus.ARCHIVED,
        }
    ),
    EntityStatus.COMPLETED: frozenset(
        {
            EntityStatus.ACTIVE,
            EntityStatus.ARCHIVED,
        }
    ),
    EntityStatus.REJECTED: frozenset(
        {
            EntityStatus.DRAFT,
            EntityStatus.ARCHIVED,
        }
    ),
    EntityStatus.ARCHIVED: frozenset(
        {
            EntityStatus.DRAFT,
        }
    ),
}


@dataclass(slots=True)
class ResearchPoint:
    """SyKaşif ekosistemindeki merkezi araştırma varlığı."""

    title: str
    location: GeoLocation
    category: ResearchCategory = ResearchCategory.GENERAL
    identity: EntityIdentity = field(
        default_factory=lambda: EntityIdentity(
            RESEARCH_POINT_PREFIX
        )
    )
    status: EntityStatus = EntityStatus.DRAFT
    description: str | None = None
    area: ResearchArea | None = None
    priority: int = 50
    tags: set[str] = field(default_factory=set)
    layers: dict[str, LayerRecord] = field(default_factory=dict)
    evidence: dict[str, EvidenceRecord] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.title = normalize_text(
            self.title,
            field_name="research_point.title",
        )

        if not 0 <= self.priority <= 100:
            raise ValueError(
                "Araştırma noktası önceliği 0 ile 100 arasında olmalıdır."
            )

        if self.area is None:
            self.area = ResearchArea(center=self.location)

        normalized_tags: set[str] = set()

        for tag in self.tags:
            normalized = tag.strip().lower()

            if normalized:
                normalized_tags.add(normalized)

        self.tags = normalized_tags

    def transition_to(self, new_status: EntityStatus) -> None:
        """Durumu izin verilen yaşam döngüsü kuralına göre değiştirir."""

        if new_status == self.status:
            return

        allowed = _ALLOWED_STATUS_TRANSITIONS[self.status]

        if new_status not in allowed:
            raise InvalidEntityStateError(
                f"{self.status.value} durumundan "
                f"{new_status.value} durumuna geçilemez."
            )

        previous_status = self.status
        self.status = new_status

        history = self.metadata.setdefault(
            "status_history",
            [],
        )
        history.append(
            {
                "from": previous_status.value,
                "to": new_status.value,
            }
        )

        self.identity.touch()

    def add_tag(self, tag: str) -> None:
        """Araştırma noktasına etiket ekler."""

        normalized = normalize_text(
            tag,
            field_name="research_point.tag",
        ).lower()

        self.tags.add(normalized)
        self.identity.touch()

    def remove_tag(self, tag: str) -> None:
        """Araştırma noktasından etiketi kaldırır."""

        self.tags.discard(tag.strip().lower())
        self.identity.touch()

    def add_layer(
        self,
        layer: LayerRecord,
        *,
        replace: bool = False,
    ) -> None:
        """Katmanı araştırma noktasına bağlar."""

        layer_id = layer.identity.syk_id or ""

        if layer_id in self.layers and not replace:
            raise ValueError(
                f"Katman zaten mevcut: {layer_id}"
            )

        self.layers[layer_id] = layer
        self.identity.touch()

    def add_layers(
        self,
        layers: Iterable[LayerRecord],
        *,
        replace: bool = False,
    ) -> None:
        """Birden fazla katmanı bağlar."""

        for layer in layers:
            self.add_layer(layer, replace=replace)

    def get_layers_by_category(
        self,
        category: LayerCategory,
    ) -> tuple[LayerRecord, ...]:
        """Belirli kategorideki katmanları öncelik sırasıyla döndürür."""

        matches = [
            layer
            for layer in self.layers.values()
            if layer.category == category
        ]

        matches.sort(
            key=lambda item: item.priority,
            reverse=True,
        )

        return tuple(matches)

    def activate_layer(self, layer_id: str) -> None:
        """Kimliği verilen katmanı etkinleştirir."""

        layer = self.layers[layer_id]
        layer.activate()
        self.identity.touch()

    def add_evidence(
        self,
        record: EvidenceRecord,
        *,
        replace: bool = False,
    ) -> None:
        """Kanıtı araştırma noktasına bağlar."""

        evidence_id = record.identity.syk_id or ""

        if evidence_id in self.evidence and not replace:
            raise DuplicateEvidenceError(
                f"Kanıt zaten mevcut: {evidence_id}"
            )

        if record.sha256_digest is not None:
            for existing in self.evidence.values():
                if (
                    existing.sha256_digest
                    == record.sha256_digest
                    and existing.identity.syk_id != evidence_id
                    and not replace
                ):
                    raise DuplicateEvidenceError(
                        "Aynı SHA-256 değerine sahip kanıt mevcut."
                    )

        self.evidence[evidence_id] = record
        self.identity.touch()

    def get_verified_evidence(
        self,
    ) -> tuple[EvidenceRecord, ...]:
        """Doğrulanmış kanıtları döndürür."""

        return tuple(
            record
            for record in self.evidence.values()
            if record.status == EvidenceStatus.VERIFIED
        )

    @property
    def visible_layers(self) -> tuple[LayerRecord, ...]:
        """Görünür katmanları öncelik sırasıyla döndürür."""

        visible = [
            layer
            for layer in self.layers.values()
            if layer.visible
        ]

        visible.sort(
            key=lambda item: item.priority,
            reverse=True,
        )

        return tuple(visible)

    @property
    def verified_evidence_count(self) -> int:
        """Doğrulanmış kanıt sayısını döndürür."""

        return len(self.get_verified_evidence())

    def summary(self) -> dict[str, Any]:
        """Runtime arayüzü için kısa özet üretir."""

        return json_safe(
            {
                "id": self.identity.syk_id,
                "title": self.title,
                "category": self.category,
                "status": self.status,
                "location": self.location.to_dict(),
                "priority": self.priority,
                "layer_count": len(self.layers),
                "visible_layer_count": len(self.visible_layers),
                "evidence_count": len(self.evidence),
                "verified_evidence_count": (
                    self.verified_evidence_count
                ),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Araştırma noktasını tam JSON uyumlu sözlüğe çevirir."""

        return json_safe(
            {
                "identity": self.identity.to_dict(),
                "title": self.title,
                "description": self.description,
                "category": self.category,
                "status": self.status,
                "priority": self.priority,
                "location": self.location.to_dict(),
                "area": (
                    self.area.to_dict()
                    if self.area is not None
                    else None
                ),
                "tags": sorted(self.tags),
                "layers": [
                    layer.to_dict()
                    for layer in self.layers.values()
                ],
                "evidence": [
                    record.to_dict()
                    for record in self.evidence.values()
                ],
                "metadata": self.metadata,
            }
        )
