from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentState:
    season: str = "summer"
    weather: str = "clear"
    daytime: str = "day"
    wind: float = 0.0


class EnvironmentManager:
    def __init__(self):
        self._state = EnvironmentState()

    @property
    def current(self) -> EnvironmentState:
        return self._state

    def update(
        self,
        *,
        season=None,
        weather=None,
        daytime=None,
        wind=None,
    ) -> EnvironmentState:
        self._state = EnvironmentState(
            season=season or self._state.season,
            weather=weather or self._state.weather,
            daytime=daytime or self._state.daytime,
            wind=self._state.wind if wind is None else float(wind),
        )

        return self._state
