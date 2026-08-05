from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class GpsFixQuality(StrEnum):
    NONE = "none"
    ESTIMATED = "estimated"
    STANDARD = "standard"
    DGPS = "dgps"
    RTK_FLOAT = "rtk-float"
    RTK_FIXED = "rtk-fixed"


@dataclass(frozen=True, slots=True)
class GpsFix:
    latitude: float
    longitude: float
    altitude_m: float | None
    accuracy_m: float | None
    quality: GpsFixQuality
    timestamp: str

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(
                "Enlem -90 ile 90 arasında olmalıdır."
            )

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(
                "Boylam -180 ile 180 arasında olmalıdır."
            )

        if (
            self.accuracy_m is not None
            and self.accuracy_m < 0
        ):
            raise ValueError(
                "GPS doğruluğu negatif olamaz."
            )

        if not self.timestamp.strip():
            raise ValueError(
                "GPS zaman bilgisi boş bırakılamaz."
            )

    @classmethod
    def create(
        cls,
        *,
        latitude: float,
        longitude: float,
        altitude_m: float | None = None,
        accuracy_m: float | None = None,
        quality: GpsFixQuality = (
            GpsFixQuality.STANDARD
        ),
    ) -> "GpsFix":
        return cls(
            latitude=latitude,
            longitude=longitude,
            altitude_m=altitude_m,
            accuracy_m=accuracy_m,
            quality=quality,
            timestamp=datetime.now(
                UTC
            ).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["quality"] = self.quality.value

        return data