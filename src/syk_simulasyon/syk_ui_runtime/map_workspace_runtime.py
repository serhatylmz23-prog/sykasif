from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from .research_runtime import research_repository


@dataclass(slots=True)
class MapPin:
    pin_id: str
    name: str
    latitude: float
    longitude: float
    altitude_m: float | None
    accuracy_m: float | None
    note: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MapLayer:
    layer_id: str
    key: str
    name: str
    layer_type: str
    visible: bool
    opacity: float
    ar_enabled: bool
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MapMeasurement:
    measurement_id: str
    measurement_type: str
    value: float
    unit: str
    start: dict[str, float]
    end: dict[str, float] | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MapWorkspace:
    workspace_id: str
    research_id: str
    name: str
    status: str
    ar_enabled: bool
    center_latitude: float
    center_longitude: float
    zoom: float
    pins: list[MapPin] = field(default_factory=list)
    layers: list[MapLayer] = field(default_factory=list)
    measurements: list[MapMeasurement] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "research_id": self.research_id,
            "name": self.name,
            "status": self.status,
            "ar_enabled": self.ar_enabled,
            "center": {
                "latitude": self.center_latitude,
                "longitude": self.center_longitude,
            },
            "zoom": self.zoom,
            "pins": [
                pin.to_dict()
                for pin in self.pins
            ],
            "layers": [
                layer.to_dict()
                for layer in self.layers
            ],
            "measurements": [
                measurement.to_dict()
                for measurement in self.measurements
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class MapWorkspaceRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._workspaces: dict[str, MapWorkspace] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _validate_coordinates(
        latitude: float,
        longitude: float,
    ) -> None:
        if not -90.0 <= latitude <= 90.0:
            raise ValueError(
                "Enlem -90 ile 90 arasında olmalıdır."
            )

        if not -180.0 <= longitude <= 180.0:
            raise ValueError(
                "Boylam -180 ile 180 arasında olmalıdır."
            )

    def reset(self) -> None:
        with self._lock:
            self._workspaces.clear()

    def create(
        self,
        *,
        research_id: str,
        name: str,
        latitude: float,
        longitude: float,
        zoom: float = 16.0,
    ) -> MapWorkspace:
        if research_repository.get(research_id) is None:
            raise LookupError(
                "Bağlı araştırma kaydı bulunamadı."
            )

        clean_name = name.strip()

        if not clean_name:
            raise ValueError(
                "Harita çalışma alanı adı boş bırakılamaz."
            )

        self._validate_coordinates(
            latitude,
            longitude,
        )

        if not 1.0 <= zoom <= 24.0:
            raise ValueError(
                "Yakınlaştırma değeri 1 ile 24 arasında olmalıdır."
            )

        now = self._now()

        workspace = MapWorkspace(
            workspace_id=str(uuid4()),
            research_id=research_id,
            name=clean_name,
            status="ready",
            ar_enabled=False,
            center_latitude=latitude,
            center_longitude=longitude,
            zoom=zoom,
            created_at=now,
            updated_at=now,
        )

        workspace.layers.extend(
            (
                MapLayer(
                    layer_id=str(uuid4()),
                    key="base-map",
                    name="Temel Harita",
                    layer_type="base",
                    visible=True,
                    opacity=1.0,
                    ar_enabled=False,
                    source="syk-map-runtime",
                ),
                MapLayer(
                    layer_id=str(uuid4()),
                    key="topography",
                    name="Topografya",
                    layer_type="terrain",
                    visible=True,
                    opacity=0.72,
                    ar_enabled=True,
                    source="syk-map-runtime",
                ),
            )
        )

        with self._lock:
            self._workspaces[
                workspace.workspace_id
            ] = workspace

        return workspace

    def get(
        self,
        workspace_id: str,
    ) -> MapWorkspace | None:
        with self._lock:
            return self._workspaces.get(workspace_id)

    def list(
        self,
        *,
        research_id: str | None = None,
    ) -> list[MapWorkspace]:
        with self._lock:
            values = list(self._workspaces.values())

        if research_id is not None:
            values = [
                workspace
                for workspace in values
                if workspace.research_id == research_id
            ]

        return sorted(
            values,
            key=lambda item: item.created_at,
        )

    def activate(
        self,
        workspace_id: str,
    ) -> MapWorkspace | None:
        with self._lock:
            workspace = self._workspaces.get(workspace_id)

            if workspace is None:
                return None

            workspace.status = "active"
            workspace.updated_at = self._now()

            return workspace

    def set_ar(
        self,
        workspace_id: str,
        *,
        enabled: bool,
    ) -> MapWorkspace | None:
        with self._lock:
            workspace = self._workspaces.get(workspace_id)

            if workspace is None:
                return None

            workspace.ar_enabled = enabled
            workspace.updated_at = self._now()

            return workspace

    def add_pin(
        self,
        workspace_id: str,
        *,
        name: str,
        latitude: float,
        longitude: float,
        altitude_m: float | None = None,
        accuracy_m: float | None = None,
        note: str = "",
    ) -> MapWorkspace | None:
        clean_name = name.strip()

        if not clean_name:
            raise ValueError(
                "Konum pini adı boş bırakılamaz."
            )

        self._validate_coordinates(
            latitude,
            longitude,
        )

        if accuracy_m is not None and accuracy_m < 0:
            raise ValueError(
                "Konum doğruluğu negatif olamaz."
            )

        with self._lock:
            workspace = self._workspaces.get(workspace_id)

            if workspace is None:
                return None

            workspace.pins.append(
                MapPin(
                    pin_id=str(uuid4()),
                    name=clean_name,
                    latitude=latitude,
                    longitude=longitude,
                    altitude_m=altitude_m,
                    accuracy_m=accuracy_m,
                    note=note.strip(),
                    created_at=self._now(),
                )
            )

            workspace.updated_at = self._now()

            return workspace

    def add_layer(
        self,
        workspace_id: str,
        *,
        key: str,
        name: str,
        layer_type: str,
        opacity: float,
        ar_enabled: bool,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> MapWorkspace | None:
        clean_key = key.strip()
        clean_name = name.strip()
        clean_type = layer_type.strip()
        clean_source = source.strip()

        if not all(
            (
                clean_key,
                clean_name,
                clean_type,
                clean_source,
            )
        ):
            raise ValueError(
                "Katman alanları boş bırakılamaz."
            )

        if not 0.0 <= opacity <= 1.0:
            raise ValueError(
                "Katman saydamlığı 0 ile 1 arasında olmalıdır."
            )

        with self._lock:
            workspace = self._workspaces.get(workspace_id)

            if workspace is None:
                return None

            existing = next(
                (
                    layer
                    for layer in workspace.layers
                    if layer.key == clean_key
                ),
                None,
            )

            if existing is not None:
                existing.name = clean_name
                existing.layer_type = clean_type
                existing.opacity = opacity
                existing.ar_enabled = ar_enabled
                existing.source = clean_source
                existing.metadata = metadata or {}
            else:
                workspace.layers.append(
                    MapLayer(
                        layer_id=str(uuid4()),
                        key=clean_key,
                        name=clean_name,
                        layer_type=clean_type,
                        visible=True,
                        opacity=opacity,
                        ar_enabled=ar_enabled,
                        source=clean_source,
                        metadata=metadata or {},
                    )
                )

            workspace.updated_at = self._now()

            return workspace

    def add_measurement(
        self,
        workspace_id: str,
        *,
        measurement_type: str,
        value: float,
        unit: str,
        start: dict[str, float],
        end: dict[str, float] | None,
    ) -> MapWorkspace | None:
        clean_type = measurement_type.strip()
        clean_unit = unit.strip()

        if not clean_type or not clean_unit:
            raise ValueError(
                "Ölçüm türü ve birimi boş bırakılamaz."
            )

        if value < 0:
            raise ValueError(
                "Ölçüm değeri negatif olamaz."
            )

        self._validate_coordinates(
            start["latitude"],
            start["longitude"],
        )

        if end is not None:
            self._validate_coordinates(
                end["latitude"],
                end["longitude"],
            )

        with self._lock:
            workspace = self._workspaces.get(workspace_id)

            if workspace is None:
                return None

            workspace.measurements.append(
                MapMeasurement(
                    measurement_id=str(uuid4()),
                    measurement_type=clean_type,
                    value=value,
                    unit=clean_unit,
                    start=start,
                    end=end,
                    created_at=self._now(),
                )
            )

            workspace.updated_at = self._now()

            return workspace


map_workspace_repository = MapWorkspaceRepository()