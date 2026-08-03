from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import urlopen


OPEN_METEO_ENDPOINT = (
    "https://api.open-meteo.com/v1/forecast"
)


WEATHER_CODE_MAP = {
    0: "clear",
    1: "partly_cloudy",
    2: "partly_cloudy",
    3: "cloudy",
    45: "fog",
    48: "fog",
    51: "rain",
    53: "rain",
    55: "rain",
    56: "rain",
    57: "rain",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    80: "rain",
    81: "rain",
    82: "rain",
    85: "snow",
    86: "snow",
    95: "storm",
    96: "storm",
    99: "storm",
}


@dataclass(frozen=True, slots=True)
class LiveEnvironmentRequest:
    latitude: float
    longitude: float
    timezone: str = "auto"

    def validate(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(
                "Enlem -90 ile 90 arasında olmalıdır."
            )

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(
                "Boylam -180 ile 180 arasında olmalıdır."
            )


class LiveEnvironmentProvider:
    def __init__(
        self,
        *,
        fetcher: Callable[
            [str],
            dict[str, Any],
        ]
        | None = None,
    ) -> None:
        self.fetcher = (
            fetcher
            or self._fetch_json
        )

    def fetch(
        self,
        request: LiveEnvironmentRequest,
    ) -> dict[str, Any]:
        request.validate()

        query = urlencode(
            {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "current": ",".join(
                    (
                        "temperature_2m",
                        "weather_code",
                        "cloud_cover",
                        "precipitation",
                        "wind_speed_10m",
                        "wind_direction_10m",
                        "is_day",
                    )
                ),
                "daily": ",".join(
                    (
                        "sunrise",
                        "sunset",
                        "daylight_duration",
                    )
                ),
                "timezone": request.timezone,
                "forecast_days": 1,
            }
        )

        raw = self.fetcher(
            f"{OPEN_METEO_ENDPOINT}?{query}"
        )

        return self._normalize(
            raw=raw,
            latitude=request.latitude,
            longitude=request.longitude,
        )

    def _normalize(
        self,
        *,
        raw: dict[str, Any],
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        current = raw.get(
            "current",
            {}
        )

        daily = raw.get(
            "daily",
            {}
        )

        weather_code = int(
            current.get(
                "weather_code",
                0,
            )
        )

        weather = WEATHER_CODE_MAP.get(
            weather_code,
            "cloudy",
        )

        cloud_percent = self._number(
            current.get(
                "cloud_cover",
                0.0,
            )
        )

        precipitation_mm = self._number(
            current.get(
                "precipitation",
                0.0,
            )
        )

        precipitation_percent = min(
            100.0,
            precipitation_mm * 25.0,
        )

        sunrise = self._first(
            daily.get(
                "sunrise"
            )
        )

        sunset = self._first(
            daily.get(
                "sunset"
            )
        )

        daylight_duration = self._number(
            self._first(
                daily.get(
                    "daylight_duration"
                )
            ),
            default=0.0,
        )

        current_time = str(
            current.get(
                "time",
                datetime.now(
                    UTC
                ).isoformat(),
            )
        )

        is_day = bool(
            int(
                current.get(
                    "is_day",
                    1,
                )
            )
        )

        daylight_factor = (
            0.82
            if is_day
            else 0.12
        )

        moon = self.moon_state(
            datetime.now(
                UTC
            )
        )

        return {
            "schema": (
                "sykasif-live-environment/v1"
            ),
            "weather": weather,
            "weather_code": weather_code,
            "temperature_c": self._number(
                current.get(
                    "temperature_2m",
                    0.0,
                )
            ),
            "wind_speed_kmh": self._number(
                current.get(
                    "wind_speed_10m",
                    0.0,
                )
            ),
            "wind_direction_deg": self._number(
                current.get(
                    "wind_direction_10m",
                    0.0,
                )
            ),
            "cloud_percent": cloud_percent,
            "precipitation_percent": (
                precipitation_percent
            ),
            "precipitation_mm": (
                precipitation_mm
            ),
            "timezone": str(
                raw.get(
                    "timezone",
                    "UTC",
                )
            ),
            "local_time": current_time,
            "sunrise": sunrise,
            "sunset": sunset,
            "daylight_duration_seconds": (
                daylight_duration
            ),
            "is_day": is_day,
            "daylight_factor": (
                daylight_factor
            ),
            "recommended_brightness": (
                self.recommended_brightness(
                    daylight_factor=(
                        daylight_factor
                    ),
                    weather=weather,
                    cloud_percent=(
                        cloud_percent
                    ),
                )
            ),
            "season": self.season(
                datetime.now(
                    UTC
                ).month
            ),
            "moon_phase": moon[
                "phase"
            ],
            "moon_illumination": moon[
                "illumination"
            ],
            "moon_age_days": moon[
                "age_days"
            ],
            "latitude": latitude,
            "longitude": longitude,
            "source": "open_meteo",
            "live_weather_connected": True,
            "field_validation_required": False,
        }

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
            "cloudy": -0.03,
            "rain": -0.06,
            "snow": 0.07,
            "fog": -0.09,
            "storm": -0.12,
        }.get(
            weather,
            0.0,
        )

        value = (
            0.48
            + daylight_factor * 0.40
            + weather_adjustment
            - min(
                0.12,
                cloud_percent
                / 100.0
                * 0.12,
            )
        )

        return round(
            min(
                1.0,
                max(
                    0.32,
                    value,
                ),
            ),
            3,
        )

    @staticmethod
    def season(month: int) -> str:
        if month in {
            12,
            1,
            2,
        }:
            return "winter"

        if month in {
            3,
            4,
            5,
        }:
            return "spring"

        if month in {
            6,
            7,
            8,
        }:
            return "summer"

        return "autumn"

    @staticmethod
    def moon_state(
        moment: datetime,
    ) -> dict[str, Any]:
        known_new_moon = datetime(
            2000,
            1,
            6,
            18,
            14,
            tzinfo=UTC,
        )

        synodic_month = (
            29.53058867
        )

        elapsed_days = (
            moment.astimezone(
                UTC
            )
            - known_new_moon
        ).total_seconds() / 86400.0

        age = (
            elapsed_days
            % synodic_month
        )

        fraction = (
            age
            / synodic_month
        )

        illumination = (
            1.0
            - math.cos(
                2.0
                * math.pi
                * fraction
            )
        ) / 2.0

        if fraction < 0.03:
            phase = "new_moon"
        elif fraction < 0.22:
            phase = "waxing_crescent"
        elif fraction < 0.28:
            phase = "first_quarter"
        elif fraction < 0.47:
            phase = "waxing_gibbous"
        elif fraction < 0.53:
            phase = "full_moon"
        elif fraction < 0.72:
            phase = "waning_gibbous"
        elif fraction < 0.78:
            phase = "last_quarter"
        else:
            phase = "waning_crescent"

        return {
            "phase": phase,
            "illumination": round(
                illumination,
                4,
            ),
            "age_days": round(
                age,
                3,
            ),
        }

    @staticmethod
    def _first(
        value: Any,
    ) -> Any:
        if (
            isinstance(
                value,
                list,
            )
            and value
        ):
            return value[0]

        return value

    @staticmethod
    def _number(
        value: Any,
        *,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _fetch_json(
        url: str,
    ) -> dict[str, Any]:
        with urlopen(
            url,
            timeout=8,
        ) as response:
            return json.loads(
                response.read().decode(
                    "utf-8"
                )
            )