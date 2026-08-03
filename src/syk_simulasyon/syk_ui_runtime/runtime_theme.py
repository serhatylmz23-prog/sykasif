from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from typing import Any

from .adaptive_theme import AdaptiveThemeResolver
from .theme_registry import ThemeRegistry


class RuntimeTheme:
    def __init__(
        self,
        registry: ThemeRegistry,
    ) -> None:
        self.registry = registry
        self.resolver = AdaptiveThemeResolver()
        self._active = "gold"
        self._mode = "automatic"
        self._lock = RLock()

    def set(
        self,
        theme_id: str,
    ) -> dict[str, Any]:
        theme = self.registry.get(theme_id)

        with self._lock:
            self._active = theme.id
            self._mode = "manual"

        return self.snapshot()

    def automatic(
        self,
        *,
        hour: int,
        weather: str,
        device: str,
    ) -> dict[str, Any]:
        theme_id = self.resolver.resolve(
            hour=hour,
            weather=weather,
            device=device,
        )

        self.registry.get(theme_id)

        with self._lock:
            self._active = theme_id
            self._mode = "automatic"

        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            theme = self.registry.get(
                self._active
            )

            mode = self._mode

        return {
            "schema": "sykasif-runtime-theme/v1",
            "active": theme.as_dict(),
            "selection_mode": mode,
            "updated_at": datetime.now(
                UTC
            ).isoformat(),
        }