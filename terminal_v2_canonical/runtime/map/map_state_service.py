from __future__ import annotations

from threading import RLock
from typing import Any

from .real_map_engine import (
    LayerState,
    MapLayer,
    MapMode,
    RealMapEngine,
)


class MapStateService:
    """
    UI <-> gerçek harita motoru arasında tek canlı durum kaynağı.

    Kurallar:
    - Sabit 2/4/8 katman sınırı yok.
    - UI'da seçilen katman motorun gerçek active_layers setine girer.
    - Seçilmeyen ağır katman suspend edilir.
    - Sağ matris yalnız motor snapshot'ından beslenir.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self.engine = RealMapEngine()

        self._seed_layers()

    def _seed_layers(self) -> None:
        defaults = [
            ("arastirma-noktalari", "Araştırma Noktaları", "harita", 100, False),
            ("fotograf", "Fotoğraf", "görüntü", 90, True),
            ("video", "Video", "görüntü", 95, True),
            ("ses", "Ses", "medya", 70, True),
            ("olcum", "Ölçüm", "bilimsel", 85, False),
            ("rota", "Rota", "harita", 80, False),
            ("iz", "İz", "harita", 79, False),
            ("kamp", "Kamp", "harita", 45, False),
            ("kazi", "Kazı", "arkeoloji", 75, False),
            ("numune", "Numune", "bilimsel", 78, False),
            ("risk", "Risk", "güvenlik", 98, False),
            ("kanit", "Kanıt", "kanıt", 99, True),
        ]

        for layer_id, title, category, priority, heavy in defaults:
            if layer_id in self.engine.layers:
                continue

            self.engine.register_layer(
                MapLayer(
                    id=layer_id,
                    title=title,
                    category=category,
                    priority=priority,
                    heavy=heavy,
                    state=LayerState.READY,
                    payload={
                        "renderer": self._renderer_for(category),
                        "source": "sykasif-runtime",
                    },
                )
            )

    @staticmethod
    def _renderer_for(category: str) -> str:
        return {
            "harita": "map-overlay",
            "görüntü": "image-video",
            "medya": "media",
            "bilimsel": "analysis",
            "arkeoloji": "analysis",
            "güvenlik": "alert",
            "kanıt": "evidence",
        }.get(category, "generic")

    @staticmethod
    def _normalise_id(value: str) -> str:
        table = str.maketrans(
            {
                "ç": "c",
                "Ç": "c",
                "ğ": "g",
                "Ğ": "g",
                "ı": "i",
                "İ": "i",
                "ö": "o",
                "Ö": "o",
                "ş": "s",
                "Ş": "s",
                "ü": "u",
                "Ü": "u",
            }
        )

        value = value.translate(table).lower().strip()

        result = []
        dash = False

        for char in value:
            if char.isalnum():
                result.append(char)
                dash = False
            elif not dash:
                result.append("-")
                dash = True

        return "".join(result).strip("-")

    def ensure_layer(
        self,
        *,
        layer_id: str,
        title: str,
        category: str = "dinamik",
        priority: int = 50,
        heavy: bool = False,
    ) -> MapLayer:
        with self._lock:
            layer_id = self._normalise_id(layer_id or title)

            existing = self.engine.layers.get(layer_id)

            if existing is not None:
                if title:
                    existing.title = title
                return existing

            layer = MapLayer(
                id=layer_id,
                title=title,
                category=category,
                priority=priority,
                heavy=heavy,
                state=LayerState.READY,
                payload={
                    "renderer": self._renderer_for(category),
                    "source": "dynamic-ui-registry",
                },
            )

            self.engine.register_layer(layer)
            return layer

    def sync_selection(
        self,
        selected: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with self._lock:
            requested: set[str] = set()

            for row in selected:
                title = str(row.get("title") or "").strip()

                if not title:
                    continue

                layer_id = self._normalise_id(
                    str(row.get("id") or title)
                )

                layer = self.ensure_layer(
                    layer_id=layer_id,
                    title=title,
                    category=str(row.get("category") or "dinamik"),
                    priority=int(row.get("priority") or 50),
                    heavy=bool(row.get("heavy", False)),
                )

                requested.add(layer.id)

            for layer in self.engine.layers.values():
                if layer.id in requested:
                    self.engine.activate_layer(layer.id)
                elif layer.visible:
                    self.engine.deactivate_layer(layer.id)

            return self.snapshot()

    def set_viewport(
        self,
        *,
        latitude: float,
        longitude: float,
        zoom: float | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self.engine.set_viewport(
                latitude=latitude,
                longitude=longitude,
                zoom=zoom,
            )

            return self.snapshot()

    def set_mode(
        self,
        mode: str,
    ) -> dict[str, Any]:
        with self._lock:
            self.engine.set_mode(MapMode(mode))
            return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            result = self.engine.snapshot()

            result["runtime"] = {
                "status": "online",
                "source": "real-map-engine",
                "matrix_count": len(result["active_layers"]),
            }

            return result


map_state_service = MapStateService()
