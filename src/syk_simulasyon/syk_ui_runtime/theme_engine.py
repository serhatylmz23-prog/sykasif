from __future__ import annotations

from typing import Any

from .asset_manager import ThemeAssetManager
from .runtime_theme import RuntimeTheme
from .theme_registry import ThemeRegistry


class ThemeEngine:
    def __init__(self) -> None:
        self.registry = ThemeRegistry()
        self.assets = ThemeAssetManager(
            self.registry
        )
        self.runtime = RuntimeTheme(
            self.registry
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "sykasif-theme-engine/v1",
            "runtime": self.runtime.snapshot(),
            "themes": self.registry.list(),
            "asset_status": {
                theme_id: self.assets.inspect(
                    theme_id
                )
                for theme_id
                in self.registry.ids()
            },
        }


theme_engine = ThemeEngine()