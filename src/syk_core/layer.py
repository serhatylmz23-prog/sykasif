"""SYK Atlas katman kayıt modeli."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .constants import LAYER_PREFIX
from .enums import LayerCategory, LayerStatus
from .errors import InvalidLayerError
from .identity import EntityIdentity
from .utils import json_safe, normalize_text, utc_now


@dataclass(slots=True)
class LayerRecord:
    """Araştırma noktasına bağlanan tek harita veya analiz katmanı."""

    name: str
    category: LayerCategory
    identity: EntityIdentity = field(
        default_factory=lambda: EntityIdentity(LAYER_PREFIX)
    )
    status: LayerStatus = LayerStatus.AVAILABLE
    visible: bool = False
    opacity: float = 1.0
    priority: int = 50
    source: str | None = None
    source_version: str | None = None
    collected_at: datetime | None = None
    temporal_start: datetime | None = None
    temporal_end: datetime | None = None
    minimum_zoom: float | None = None
    maximum_zoom: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = normalize_text(
            self.name,
            field_name="layer.name",
        )

        self.opacity = float(self.opacity)

        if not 0.0 <= self.opacity <= 1.0:
            raise InvalidLayerError(
                "Katman opaklığı 0.0 ile 1.0 arasında olmalıdır."
            )

        if not 0 <= self.priority <= 100:
            raise InvalidLayerError(
                "Katman önceliği 0 ile 100 arasında olmalıdır."
            )

        if (
            self.minimum_zoom is not None
            and self.maximum_zoom is not None
            and self.minimum_zoom > self.maximum_zoom
        ):
            raise InvalidLayerError(
                "minimum_zoom, maximum_zoom değerinden büyük olamaz."
            )

        if (
            self.temporal_start is not None
            and self.temporal_end is not None
            and self.temporal_start > self.temporal_end
        ):
            raise InvalidLayerError(
                "Katman zaman başlangıcı bitişten sonra olamaz."
            )

        if self.visible and self.status == LayerStatus.UNAVAILABLE:
            raise InvalidLayerError(
                "Kullanılamayan katman görünür yapılamaz."
            )

    @property
    def is_temporal(self) -> bool:
        """Katmanın zaman aralığı içerip içermediğini döndürür."""

        return (
            self.temporal_start is not None
            or self.temporal_end is not None
            or self.category == LayerCategory.TEMPORAL
        )

    def activate(self) -> None:
        """Katmanı görünür ve aktif yapar."""

        if self.status in {
            LayerStatus.UNAVAILABLE,
            LayerStatus.ERROR,
        }:
            raise InvalidLayerError(
                f"{self.status.value} durumundaki katman etkinleştirilemez."
            )

        self.visible = True
        self.status = LayerStatus.ACTIVE
        self.identity.touch()

    def hide(self) -> None:
        """Katmanı görünümden kaldırır."""

        self.visible = False

        if self.status == LayerStatus.ACTIVE:
            self.status = LayerStatus.HIDDEN

        self.identity.touch()

    def set_opacity(self, value: float) -> None:
        """Katman opaklığını günceller."""

        opacity = float(value)

        if not 0.0 <= opacity <= 1.0:
            raise InvalidLayerError(
                "Katman opaklığı 0.0 ile 1.0 arasında olmalıdır."
            )

        self.opacity = opacity
        self.identity.touch()

    def mark_loading(self) -> None:
        """Katmanı yükleniyor durumuna geçirir."""

        self.status = LayerStatus.LOADING
        self.identity.touch()

    def mark_error(self, message: str) -> None:
        """Katmanı hata durumuna geçirir."""

        self.status = LayerStatus.ERROR
        self.visible = False
        self.metadata["error"] = normalize_text(
            message,
            field_name="layer.error",
        )
        self.metadata["error_at"] = utc_now()
        self.identity.touch()

    def to_dict(self) -> dict[str, Any]:
        """Katmanı JSON uyumlu sözlüğe dönüştürür."""

        return json_safe(
            {
                "identity": self.identity.to_dict(),
                "name": self.name,
                "category": self.category,
                "status": self.status,
                "visible": self.visible,
                "opacity": self.opacity,
                "priority": self.priority,
                "source": self.source,
                "source_version": self.source_version,
                "collected_at": self.collected_at,
                "temporal_start": self.temporal_start,
                "temporal_end": self.temporal_end,
                "minimum_zoom": self.minimum_zoom,
                "maximum_zoom": self.maximum_zoom,
                "is_temporal": self.is_temporal,
                "metadata": self.metadata,
            }
        )
