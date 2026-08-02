from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    id: str
    title: str


THEMES = {
    "day": Theme("day", "Gündüz"),
    "night": Theme("night", "Gece"),
    "sunrise": Theme("sunrise", "Gün Doğumu"),
    "sunset": Theme("sunset", "Gün Batımı"),
    "rain": Theme("rain", "Yağmur"),
    "snow": Theme("snow", "Kar"),
    "fog": Theme("fog", "Sis"),
}


class ThemeManager:
    def __init__(self):
        self._theme = "day"

    @property
    def current(self) -> Theme:
        return THEMES[self._theme]

    def set(self, theme_id: str) -> Theme:
        if theme_id not in THEMES:
            raise KeyError(f"Unknown theme: {theme_id}")

        self._theme = theme_id
        return self.current

    def available(self) -> list[Theme]:
        return list(THEMES.values())
