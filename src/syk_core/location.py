"""Konum ve araştırma alanı modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt
from typing import Iterable

from .constants import (
    DEFAULT_COORDINATE_SYSTEM,
    DEFAULT_SEARCH_RADIUS_METERS,
    MAX_ACCURACY_METERS,
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_SEARCH_RADIUS_METERS,
    MIN_ACCURACY_METERS,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    MIN_SEARCH_RADIUS_METERS,
)
from .enums import AccuracySource
from .errors import InvalidCoordinateError


def _validate_latitude(value: float) -> float:
    latitude = float(value)

    if not MIN_LATITUDE <= latitude <= MAX_LATITUDE:
        raise InvalidCoordinateError(
            f"Enlem {MIN_LATITUDE} ile {MAX_LATITUDE} arasında olmalıdır."
        )

    return latitude


def _validate_longitude(value: float) -> float:
    longitude = float(value)

    if not MIN_LONGITUDE <= longitude <= MAX_LONGITUDE:
        raise InvalidCoordinateError(
            f"Boylam {MIN_LONGITUDE} ile {MAX_LONGITUDE} arasında olmalıdır."
        )

    return longitude


def _validate_accuracy(value: float | None) -> float | None:
    if value is None:
        return None

    accuracy = float(value)

    if not MIN_ACCURACY_METERS <= accuracy <= MAX_ACCURACY_METERS:
        raise InvalidCoordinateError(
            "Konum doğruluğu geçerli sınırlar dışında."
        )

    return accuracy


@dataclass(slots=True, frozen=True)
class GeoLocation:
    """Tek bir coğrafi koordinat."""

    latitude: float
    longitude: float
    altitude_m: float | None = None
    horizontal_accuracy_m: float | None = None
    vertical_accuracy_m: float | None = None
    accuracy_source: AccuracySource = AccuracySource.UNKNOWN
    coordinate_system: str = DEFAULT_COORDINATE_SYSTEM

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "latitude",
            _validate_latitude(self.latitude),
        )
        object.__setattr__(
            self,
            "longitude",
            _validate_longitude(self.longitude),
        )
        object.__setattr__(
            self,
            "horizontal_accuracy_m",
            _validate_accuracy(self.horizontal_accuracy_m),
        )
        object.__setattr__(
            self,
            "vertical_accuracy_m",
            _validate_accuracy(self.vertical_accuracy_m),
        )

        if self.altitude_m is not None:
            object.__setattr__(
                self,
                "altitude_m",
                float(self.altitude_m),
            )

        coordinate_system = self.coordinate_system.strip()

        if not coordinate_system:
            raise InvalidCoordinateError(
                "Koordinat sistemi boş olamaz."
            )

        object.__setattr__(
            self,
            "coordinate_system",
            coordinate_system,
        )

    def distance_to(self, other: "GeoLocation") -> float:
        """İki koordinat arasındaki yaklaşık yüzey mesafesini metre döndürür."""

        earth_radius_m = 6_371_008.8

        lat1 = radians(self.latitude)
        lon1 = radians(self.longitude)
        lat2 = radians(other.latitude)
        lon2 = radians(other.longitude)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        angular_distance = 2 * asin(sqrt(a))

        return earth_radius_m * angular_distance

    def to_dict(self) -> dict[str, object]:
        """Konumu JSON uyumlu sözlüğe çevirir."""

        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "horizontal_accuracy_m": self.horizontal_accuracy_m,
            "vertical_accuracy_m": self.vertical_accuracy_m,
            "accuracy_source": self.accuracy_source.value,
            "coordinate_system": self.coordinate_system,
        }


@dataclass(slots=True)
class ResearchArea:
    """Araştırma merkezini, yarıçapını veya poligon sınırını tanımlar."""

    center: GeoLocation
    radius_m: float = DEFAULT_SEARCH_RADIUS_METERS
    polygon: tuple[GeoLocation, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self.radius_m = float(self.radius_m)

        if not (
            MIN_SEARCH_RADIUS_METERS
            <= self.radius_m
            <= MAX_SEARCH_RADIUS_METERS
        ):
            raise InvalidCoordinateError(
                "Araştırma yarıçapı geçerli sınırlar dışında."
            )

        if self.polygon and len(self.polygon) < 3:
            raise InvalidCoordinateError(
                "Alan poligonu en az üç koordinat içermelidir."
            )

    @classmethod
    def from_polygon(
        cls,
        center: GeoLocation,
        polygon: Iterable[GeoLocation],
        *,
        radius_m: float = DEFAULT_SEARCH_RADIUS_METERS,
    ) -> "ResearchArea":
        """Koordinat listesinden araştırma alanı oluşturur."""

        return cls(
            center=center,
            radius_m=radius_m,
            polygon=tuple(polygon),
        )

    @property
    def mode(self) -> str:
        """Alan seçim yöntemini döndürür."""

        if self.polygon:
            return "polygon"

        return "radius"

    def contains_approximately(
        self,
        location: GeoLocation,
    ) -> bool:
        """Yarıçap tabanlı yaklaşık içerme kontrolü yapar."""

        return self.center.distance_to(location) <= self.radius_m

    def to_dict(self) -> dict[str, object]:
        """Araştırma alanını JSON uyumlu sözlüğe çevirir."""

        return {
            "center": self.center.to_dict(),
            "radius_m": self.radius_m,
            "mode": self.mode,
            "polygon": [
                coordinate.to_dict()
                for coordinate in self.polygon
            ],
        }
