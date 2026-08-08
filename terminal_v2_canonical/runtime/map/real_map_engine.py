from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MapMode(StrEnum):
    MAP = "harita"
    SATELLITE = "uydu"
    TERRAIN = "arazi"
    TOPOGRAPHIC = "topografya"


class LayerState(StrEnum):
    UNLOADED = "unloaded"
    READY = "ready"
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass(slots=True, frozen=True)
class GeoPoint:
    latitude: float
    longitude: float


@dataclass(slots=True)
class MapLayer:
    id: str
    title: str
    category: str
    priority: int = 0
    heavy: bool = False
    visible: bool = False
    state: LayerState = LayerState.UNLOADED
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MapViewport:
    center: GeoPoint
    zoom: float = 10.0
    mode: MapMode = MapMode.MAP


class RealMapEngine:
    """
    SyKaşif gerçek harita motoru çekirdeği.

    Bu sınıf:
    - kanonik UI'dan bağımsızdır,
    - taban harita durumunu tutar,
    - gerçek katman kayıtlarını yönetir,
    - yalnız etkin katmanları çalışma setine alır,
    - sağ dinamik matris için sıralı görünür katman üretir.
    """

    def __init__(self) -> None:
        self.viewport = MapViewport(
            center=GeoPoint(
                latitude=39.0,
                longitude=35.0,
            ),
            zoom=6.0,
        )

        self.layers: dict[str, MapLayer] = {}

    def set_viewport(
        self,
        *,
        latitude: float,
        longitude: float,
        zoom: float | None = None,
    ) -> MapViewport:
        self.viewport.center = GeoPoint(
            latitude=latitude,
            longitude=longitude,
        )

        if zoom is not None:
            self.viewport.zoom = zoom

        return self.viewport

    def set_mode(
        self,
        mode: MapMode,
    ) -> MapMode:
        self.viewport.mode = mode
        return self.viewport.mode

    def register_layer(
        self,
        layer: MapLayer,
    ) -> None:
        if layer.id in self.layers:
            raise ValueError(
                f"KATMAN_ZATEN_KAYITLI:{layer.id}"
            )

        self.layers[layer.id] = layer

    def activate_layer(
        self,
        layer_id: str,
    ) -> MapLayer:
        layer = self.layers[layer_id]

        layer.visible = True
        layer.state = LayerState.ACTIVE

        return layer

    def deactivate_layer(
        self,
        layer_id: str,
    ) -> MapLayer:
        layer = self.layers[layer_id]

        layer.visible = False

        layer.state = (
            LayerState.SUSPENDED
            if layer.heavy
            else LayerState.READY
        )

        return layer

    def active_layers(
        self,
    ) -> list[MapLayer]:
        return sorted(
            (
                layer
                for layer in self.layers.values()
                if layer.visible
                and layer.state == LayerState.ACTIVE
            ),
            key=lambda item: (
                -item.priority,
                item.title,
            ),
        )

    def matrix_payload(
        self,
    ) -> list[dict[str, Any]]:
        """
        Sağ dinamik matris için gerçek veri sözleşmesi.
        Sabit 2/4/8 sınırı yoktur.
        """
        return [
            {
                "id": layer.id,
                "title": layer.title,
                "category": layer.category,
                "priority": layer.priority,
                "heavy": layer.heavy,
                "state": layer.state.value,
                "payload": layer.payload,
            }
            for layer in self.active_layers()
        ]

    def snapshot(
        self,
    ) -> dict[str, Any]:
        return {
            "viewport": {
                "latitude": self.viewport.center.latitude,
                "longitude": self.viewport.center.longitude,
                "zoom": self.viewport.zoom,
                "mode": self.viewport.mode.value,
            },
            "active_layers": self.matrix_payload(),
            "registered_layer_count": len(self.layers),
        }
