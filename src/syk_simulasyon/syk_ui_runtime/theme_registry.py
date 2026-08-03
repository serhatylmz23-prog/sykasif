from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


THEME_IDS = (
    "gold",
    "silver",
    "dark",
    "tablet",
    "mobile",
    "print",
    "splash",
    "loading",
)


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    id: str
    title: str
    mode: str
    colors: dict[str, str]
    assets: dict[str, str]
    root: Path

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "mode": self.mode,
            "colors": dict(self.colors),
            "assets": {
                name: (
                    f"/api/syk-ui/themes/"
                    f"{self.id}/assets/{filename}"
                )
                for name, filename
                in self.assets.items()
            },
        }


class ThemeRegistry:
    def __init__(
        self,
        root: str | Path | None = None,
    ) -> None:
        self.root = (
            Path(root)
            if root is not None
            else Path(__file__).resolve().parent
            / "assets"
            / "themes"
        )

        self._themes: dict[
            str,
            ThemeDefinition,
        ] = {}

        self.reload()

    def reload(self) -> None:
        themes: dict[
            str,
            ThemeDefinition,
        ] = {}

        for theme_id in THEME_IDS:
            theme_root = self.root / theme_id
            manifest_path = (
                theme_root / "theme.json"
            )

            if not manifest_path.is_file():
                continue

            if manifest_path.stat().st_size == 0:
                continue

            payload = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            themes[theme_id] = ThemeDefinition(
                id=str(payload["id"]),
                title=str(payload["title"]),
                mode=str(payload["mode"]),
                colors={
                    str(key): str(value)
                    for key, value
                    in payload["colors"].items()
                },
                assets={
                    str(key): str(value)
                    for key, value
                    in payload["assets"].items()
                },
                root=theme_root,
            )

        self._themes = themes

    def ids(self) -> tuple[str, ...]:
        return tuple(self._themes)

    def list(self) -> list[dict[str, Any]]:
        return [
            theme.as_dict()
            for theme in self._themes.values()
        ]

    def get(
        self,
        theme_id: str,
    ) -> ThemeDefinition:
        try:
            return self._themes[theme_id]
        except KeyError as error:
            raise KeyError(
                f"Bilinmeyen tema: {theme_id}"
            ) from error