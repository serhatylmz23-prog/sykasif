"""GPS veya kullanıcı işaretli pin oluşturma akışı."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .enums import (
    AccuracySource,
    EntityStatus,
    ResearchCategory,
)
from .layer_repository import InMemoryLayerRepository
from .location import GeoLocation, ResearchArea
from .location_selector import (
    LayerSelectionResult,
    LocationLayerSelector,
)
from .research_point import ResearchPoint


class PinSource(StrEnum):
    """Araştırma pininin oluşturulma kaynağı."""

    LIVE_GPS = "live_gps"
    RTK = "rtk"
    MANUAL_MAP = "manual_map"
    COORDINATE_INPUT = "coordinate_input"
    IMPORTED = "imported"


@dataclass(slots=True, frozen=True)
class PinCreationRequest:
    """Araştırma pini oluşturma isteği."""

    title: str
    latitude: float
    longitude: float
    category: ResearchCategory
    source: PinSource
    altitude_m: float | None = None
    horizontal_accuracy_m: float | None = None
    vertical_accuracy_m: float | None = None
    radius_m: float = 100.0
    online_available: bool = False
    device_data_available: bool = False
    description: str | None = None
    priority: int = 50
    tags: frozenset[str] = frozenset()
    metadata: dict[str, Any] | None = None

    def resolve_accuracy_source(self) -> AccuracySource:
        """Pin kaynağını konum doğruluk kaynağına dönüştürür."""

        mapping = {
            PinSource.LIVE_GPS: AccuracySource.DEVICE_GPS,
            PinSource.RTK: AccuracySource.RTK_FIXED,
            PinSource.MANUAL_MAP: AccuracySource.MANUAL,
            PinSource.COORDINATE_INPUT: AccuracySource.MANUAL,
            PinSource.IMPORTED: AccuracySource.IMPORTED,
        }

        return mapping[self.source]


@dataclass(slots=True)
class PinCreationResult:
    """Pin oluşturma işlem sonucu."""

    research_point: ResearchPoint
    selection: LayerSelectionResult
    repository: InMemoryLayerRepository

    @property
    def activated_layer_count(self) -> int:
        return len(self.selection.automatic_layer_ids)


class ResearchPinFlow:
    """Pin oluşturur, katman seçer ve araştırma noktasına bağlar."""

    def __init__(
        self,
        selector: LocationLayerSelector,
    ) -> None:
        self._selector = selector

    def create(
        self,
        request: PinCreationRequest,
    ) -> PinCreationResult:
        """GPS veya harita işaretinden araştırma noktası üretir."""

        location = GeoLocation(
            latitude=request.latitude,
            longitude=request.longitude,
            altitude_m=request.altitude_m,
            horizontal_accuracy_m=(
                request.horizontal_accuracy_m
            ),
            vertical_accuracy_m=request.vertical_accuracy_m,
            accuracy_source=request.resolve_accuracy_source(),
        )

        area = ResearchArea(
            center=location,
            radius_m=request.radius_m,
        )

        selection = self._selector.select(
            area=area,
            research_category=request.category,
            online_available=request.online_available,
            device_data_available=request.device_data_available,
        )

        point = ResearchPoint(
            title=request.title,
            description=request.description,
            location=location,
            area=area,
            category=request.category,
            priority=request.priority,
            tags=set(request.tags),
            metadata={
                "pin_source": request.source.value,
                **(request.metadata or {}),
            },
        )

        repository = InMemoryLayerRepository()

        for layer in selection.selected_layers:
            point.add_layer(layer)
            repository.add(layer)

        point.transition_to(EntityStatus.ACTIVE)

        return PinCreationResult(
            research_point=point,
            selection=selection,
            repository=repository,
        )
