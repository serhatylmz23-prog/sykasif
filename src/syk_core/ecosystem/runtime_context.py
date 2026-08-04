"""Dinamik canlı ekosistem çalışma bağlamı."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..location import GeoLocation
from ..utils import utc_now
from .enums import (
    SalinityType,
    WaterBodyType,
)


@dataclass(slots=True, frozen=True)
class EcosystemRuntimeContext:
    """Balık ve bitki motorlarının ortak çalışma bağlamı."""

    location: GeoLocation
    region_code: str
    region_name: str
    observed_at: datetime = field(default_factory=utc_now)

    salinity: SalinityType = SalinityType.UNKNOWN
    water_body_type: WaterBodyType = WaterBodyType.UNKNOWN
    water_body_name: str | None = None

    depth_m: float | None = None
    water_temperature_c: float | None = None
    dissolved_oxygen_mg_l: float | None = None
    ph_value: float | None = None
    conductivity_us_cm: float | None = None

    altitude_m: float | None = None
    air_temperature_c: float | None = None
    soil_moisture_percent: float | None = None
    relative_humidity_percent: float | None = None
    slope_degree: float | None = None

    online_available: bool = False
    device_data_available: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.region_code.strip():
            raise ValueError(
                "Bölge kodu boş olamaz."
            )

        if not self.region_name.strip():
            raise ValueError(
                "Bölge adı boş olamaz."
            )

        for field_name in (
            "depth_m",
            "altitude_m",
            "soil_moisture_percent",
            "relative_humidity_percent",
            "slope_degree",
        ):
            value = getattr(self, field_name)

            if value is not None and float(value) < 0:
                raise ValueError(
                    f"{field_name} negatif olamaz."
                )

        for field_name in (
            "soil_moisture_percent",
            "relative_humidity_percent",
        ):
            value = getattr(self, field_name)

            if value is not None and float(value) > 100:
                raise ValueError(
                    f"{field_name} 100 değerinden büyük olamaz."
                )

        if (
            self.ph_value is not None
            and not 0.0 <= float(self.ph_value) <= 14.0
        ):
            raise ValueError(
                "pH değeri 0 ile 14 arasında olmalıdır."
            )

    @property
    def month(self) -> int:
        return self.observed_at.month

    @property
    def is_keban_reservoir(self) -> bool:
        water_name = (
            self.water_body_name or ""
        ).casefold()

        return (
            "keban" in water_name
            and self.water_body_type
            == WaterBodyType.RESERVOIR
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "konum": self.location.to_dict(),
            "bölge_kodu": self.region_code,
            "bölge_adı": self.region_name,
            "gözlem_zamanı": self.observed_at.isoformat(),
            "ay": self.month,
            "tuzluluk": self.salinity.value,
            "su_kütlesi_türü": self.water_body_type.value,
            "su_kütlesi_adı": self.water_body_name,
            "derinlik_m": self.depth_m,
            "su_sıcaklığı_c": self.water_temperature_c,
            "çözünmüş_oksijen_mg_l": (
                self.dissolved_oxygen_mg_l
            ),
            "ph": self.ph_value,
            "iletkenlik_us_cm": self.conductivity_us_cm,
            "rakım_m": self.altitude_m,
            "hava_sıcaklığı_c": self.air_temperature_c,
            "toprak_nemi_yüzde": (
                self.soil_moisture_percent
            ),
            "bağıl_nem_yüzde": (
                self.relative_humidity_percent
            ),
            "eğim_derece": self.slope_degree,
            "çevrimiçi": self.online_available,
            "cihaz_verisi": self.device_data_available,
            "üst_veri": self.metadata,
        }
