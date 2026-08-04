"""OVM ana varlık modeli."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from ..location import GeoLocation
from ..utils import json_safe, utc_now
from .enums import (
    ConfidenceLevel,
    EntityKind,
    RuntimeState,
    VisualStatus,
)
from .localization import (
    ensure_utf8_text,
    get_turkish_label,
)


@dataclass(slots=True)
class OvmEntityIdentity:
    """OVM varlık kimliği."""

    uuid: UUID = field(default_factory=uuid4)
    entity_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.entity_id is None:
            self.entity_id = (
                f"SYK-OVM-{self.uuid.hex[:16].upper()}"
            )

        self.entity_id = ensure_utf8_text(self.entity_id)

        if self.updated_at < self.created_at:
            raise ValueError(
                "Güncelleme zamanı oluşturma zamanından önce olamaz."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "entity_id": self.entity_id,
                "uuid": self.uuid,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )


@dataclass(slots=True)
class OvmEntity:
    """SyKaşif modüllerinin ortak varlık nesnesi."""

    kind: EntityKind
    title: str
    identity: OvmEntityIdentity = field(
        default_factory=OvmEntityIdentity
    )
    description: str | None = None
    location: GeoLocation | None = None

    parent_id: str | None = None
    child_ids: set[str] = field(default_factory=set)
    related_entity_ids: set[str] = field(default_factory=set)

    layer_code: str | None = None
    layer_order: int = 0
    visible: bool = True
    opacity: float = 1.0

    runtime_state: RuntimeState = RuntimeState.NEW
    visual_status: VisualStatus = VisualStatus.NEUTRAL
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    confidence_score: float | None = None

    icon_code: str | None = None
    dynamic_style: dict[str, Any] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.title = ensure_utf8_text(self.title)

        if self.description is not None:
            self.description = ensure_utf8_text(
                self.description
            )

        self.opacity = float(self.opacity)

        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError(
                "Varlık opaklığı 0.0 ile 1.0 arasında olmalıdır."
            )

        if self.layer_order < 0:
            raise ValueError(
                "Katman sırası negatif olamaz."
            )

        if self.confidence_score is not None:
            self.set_confidence_score(
                self.confidence_score
            )

        self.tags = {
            ensure_utf8_text(tag).lower()
            for tag in self.tags
        }

    @property
    def entity_id(self) -> str:
        return self.identity.entity_id or ""

    @property
    def turkish_kind(self) -> str:
        return get_turkish_label(self.kind)

    @property
    def turkish_runtime_state(self) -> str:
        return get_turkish_label(
            self.runtime_state
        )

    @property
    def turkish_visual_status(self) -> str:
        return get_turkish_label(
            self.visual_status
        )

    def set_runtime_state(
        self,
        state: RuntimeState,
    ) -> None:
        self.runtime_state = state
        self.identity.touch()

    def set_visual_status(
        self,
        status: VisualStatus,
    ) -> None:
        self.visual_status = status
        self.identity.touch()

    def set_confidence_score(
        self,
        score: float,
    ) -> None:
        normalized = float(score)

        if not 0.0 <= normalized <= 100.0:
            raise ValueError(
                "Güven skoru 0 ile 100 arasında olmalıdır."
            )

        self.confidence_score = normalized

        if normalized < 20:
            self.confidence_level = ConfidenceLevel.VERY_LOW
        elif normalized < 40:
            self.confidence_level = ConfidenceLevel.LOW
        elif normalized < 60:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif normalized < 80:
            self.confidence_level = ConfidenceLevel.HIGH
        elif normalized < 99.9:
            self.confidence_level = ConfidenceLevel.VERY_HIGH
        else:
            self.confidence_level = ConfidenceLevel.VERIFIED

        self.identity.touch()

    def add_child(
        self,
        child_id: str,
    ) -> None:
        normalized = ensure_utf8_text(child_id)

        if normalized == self.entity_id:
            raise ValueError(
                "Varlık kendisini alt varlık olarak ekleyemez."
            )

        self.child_ids.add(normalized)
        self.identity.touch()

    def add_relation(
        self,
        entity_id: str,
    ) -> None:
        normalized = ensure_utf8_text(entity_id)

        if normalized == self.entity_id:
            raise ValueError(
                "Varlık kendisiyle ilişkilendirilemez."
            )

        self.related_entity_ids.add(normalized)
        self.identity.touch()

    def set_dynamic_style(
        self,
        **values: Any,
    ) -> None:
        self.dynamic_style.update(values)
        self.identity.touch()

    def to_runtime_dict(self) -> dict[str, Any]:
        """Türkçe arayüzde doğrudan kullanılacak veri."""

        return json_safe(
            {
                "id": self.entity_id,
                "tür": self.turkish_kind,
                "başlık": self.title,
                "açıklama": self.description,
                "çalışma_durumu": (
                    self.turkish_runtime_state
                ),
                "görsel_durum": (
                    self.turkish_visual_status
                ),
                "güven_düzeyi": get_turkish_label(
                    self.confidence_level
                ),
                "güven_skoru": self.confidence_score,
                "görünür": self.visible,
                "opaklık": self.opacity,
                "ikon": self.icon_code,
                "katman": self.layer_code,
                "dinamik_stil": self.dynamic_style,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "identity": self.identity.to_dict(),
                "kind": self.kind,
                "title": self.title,
                "description": self.description,
                "location": (
                    self.location.to_dict()
                    if self.location is not None
                    else None
                ),
                "parent_id": self.parent_id,
                "child_ids": sorted(self.child_ids),
                "related_entity_ids": sorted(
                    self.related_entity_ids
                ),
                "layer_code": self.layer_code,
                "layer_order": self.layer_order,
                "visible": self.visible,
                "opacity": self.opacity,
                "runtime_state": self.runtime_state,
                "visual_status": self.visual_status,
                "confidence_level": self.confidence_level,
                "confidence_score": self.confidence_score,
                "icon_code": self.icon_code,
                "dynamic_style": self.dynamic_style,
                "tags": sorted(self.tags),
                "metadata": self.metadata,
            }
        )
