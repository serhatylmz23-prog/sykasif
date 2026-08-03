from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
import os
from threading import RLock
from typing import Any
from zoneinfo import ZoneInfo


WEATHER_STATES = {
    "clear",
    "partly_cloudy",
    "cloudy",
    "rain",
    "snow",
    "fog",
    "storm",
}

SEASONS = {
    "winter",
    "spring",
    "summer",
    "autumn",
}


@dataclass(frozen=True, slots=True)
class EnvironmentState:
    weather: str
    temperature_c: float
    wind_speed_kmh: float
    wind_direction_deg: float
    cloud_percent: float
    precipitation_percent: float
    timezone: str
    latitude: float | None
    longitude: float | None
    source: str

    def as_dict(self) -> dict[str, Any]:
        local_time = datetime.now(
            ZoneInfo(self.timezone)
        )

        daylight = AdaptiveEnvironmentEngine.daylight_factor(
            hour=local_time.hour,
            minute=local_time.minute,
        )

        return {
            "schema": "sykasif-adaptive-environment/v1",
            "weather": self.weather,
            "temperature_c": round(
                self.temperature_c,
                2,
            ),
            "wind_speed_kmh": round(
                self.wind_speed_kmh,
                2,
            ),
            "wind_direction_deg": round(
                self.wind_direction_deg % 360.0,
                2,
            ),
            "cloud_percent": round(
                min(
                    100.0,
                    max(
                        0.0,
                        self.cloud_percent,
                    ),
                ),
                2,
            ),
            "precipitation_percent": round(
                min(
                    100.0,
                    max(
                        0.0,
                        self.precipitation_percent,
                    ),
                ),
                2,
            ),
            "timezone": self.timezone,
            "local_time": local_time.isoformat(),
            "hour": local_time.hour,
            "minute": local_time.minute,
            "season": AdaptiveEnvironmentEngine.season(
                local_time.month
            ),
            "daylight_factor": daylight,
            "recommended_brightness": round(
                AdaptiveEnvironmentEngine.recommended_brightness(
                    daylight_factor=daylight,
                    weather=self.weather,
                    cloud_percent=self.cloud_percent,
                ),
                3,
            ),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "source": self.source,
            "live_weather_connected": (
                self.source != "local_fallback"
            ),
        }


class AdaptiveEnvironmentEngine:
    def __init__(self) -> None:
        self._lock = RLock()
        self._manual_state: EnvironmentState | None = None

    def current(self) -> dict[str, Any]:
        with self._lock:
            state = (
                self._manual_state
                or self._fallback_state()
            )

        return state.as_dict()

    def update(
        self,
        *,
        weather: str,
        temperature_c: float,
        wind_speed_kmh: float,
        wind_direction_deg: float,
        cloud_percent: float,
        precipitation_percent: float,
        timezone: str = "Europe/Istanbul",
        latitude: float | None = None,
        longitude: float | None = None,
        source: str = "manual_runtime",
    ) -> dict[str, Any]:
        if weather not in WEATHER_STATES:
            raise ValueError(
                "Geçersiz meteoroloji durumu."
            )

        if wind_speed_kmh < 0:
            raise ValueError(
                "Rüzgâr hızı negatif olamaz."
            )

        ZoneInfo(timezone)

        state = EnvironmentState(
            weather=weather,
            temperature_c=float(
                temperature_c
            ),
            wind_speed_kmh=float(
                wind_speed_kmh
            ),
            wind_direction_deg=float(
                wind_direction_deg
            ),
            cloud_percent=float(
                cloud_percent
            ),
            precipitation_percent=float(
                precipitation_percent
            ),
            timezone=timezone,
            latitude=latitude,
            longitude=longitude,
            source=source,
        )

        with self._lock:
            self._manual_state = state

        return state.as_dict()

    def clear_manual(self) -> dict[str, Any]:
        with self._lock:
            self._manual_state = None

        return self.current()

    def _fallback_state(self) -> EnvironmentState:
        timezone = os.getenv(
            "SYK_ENV_TIMEZONE",
            "Europe/Istanbul",
        )

        weather = os.getenv(
            "SYK_ENV_WEATHER",
            "clear",
        )

        if weather not in WEATHER_STATES:
            weather = "clear"

        return EnvironmentState(
            weather=weather,
            temperature_c=float(
                os.getenv(
                    "SYK_ENV_TEMPERATURE_C",
                    "22.0",
                )
            ),
            wind_speed_kmh=float(
                os.getenv(
                    "SYK_ENV_WIND_KMH",
                    "5.0",
                )
            ),
            wind_direction_deg=float(
                os.getenv(
                    "SYK_ENV_WIND_DEG",
                    "0.0",
                )
            ),
            cloud_percent=float(
                os.getenv(
                    "SYK_ENV_CLOUD_PERCENT",
                    "10.0",
                )
            ),
            precipitation_percent=float(
                os.getenv(
                    "SYK_ENV_PRECIPITATION_PERCENT",
                    "0.0",
                )
            ),
            timezone=timezone,
            latitude=None,
            longitude=None,
            source="local_fallback",
        )

    @staticmethod
    def season(month: int) -> str:
        if month in {12, 1, 2}:
            return "winter"

        if month in {3, 4, 5}:
            return "spring"

        if month in {6, 7, 8}:
            return "summer"

        return "autumn"

    @staticmethod
    def daylight_factor(
        *,
        hour: int,
        minute: int,
    ) -> float:
        decimal_hour = (
            hour
            + minute / 60.0
        )

        sunrise = 6.0
        sunset = 19.5

        if (
            decimal_hour <= sunrise
            or decimal_hour >= sunset
        ):
            return 0.12

        normalized = (
            decimal_hour - sunrise
        ) / (
            sunset - sunrise
        )

        daylight = math.sin(
            normalized * math.pi
        )

        return round(
            max(
                0.12,
                min(
                    1.0,
                    daylight,
                ),
            ),
            4,
        )

    @staticmethod
    def recommended_brightness(
        *,
        daylight_factor: float,
        weather: str,
        cloud_percent: float,
    ) -> float:
        weather_adjustment = {
            "clear": 0.08,
            "partly_cloudy": 0.03,
            "cloudy": -0.04,
            "rain": -0.06,
            "snow": 0.08,
            "fog": -0.10,
            "storm": -0.12,
        }[weather]

        cloud_adjustment = (
            -0.12
            * min(
                1.0,
                max(
                    0.0,
                    cloud_percent / 100.0,
                ),
            )
        )

        value = (
            0.52
            + daylight_factor * 0.35
            + weather_adjustment
            + cloud_adjustment
        )

        return max(
            0.32,
            min(
                1.0,
                value,
            ),
        )