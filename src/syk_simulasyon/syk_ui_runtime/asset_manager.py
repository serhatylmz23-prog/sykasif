from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from .theme_registry import ThemeRegistry


class ThemeAssetManager:
    def __init__(
        self,
        registry: ThemeRegistry,
    ) -> None:
        self.registry = registry

    def resolve(
        self,
        theme_id: str,
        filename: str,
    ) -> Path:
        theme = self.registry.get(theme_id)

        safe_name = Path(filename).name

        if safe_name != filename:
            raise ValueError(
                "Geçersiz tema varlığı yolu."
            )

        path = theme.root / safe_name

        if not path.is_file():
            raise FileNotFoundError(path)

        if path.stat().st_size == 0:
            raise FileNotFoundError(
                f"Boş tema varlığı: {path}"
            )

        return path

    def inspect(
        self,
        theme_id: str,
    ) -> dict[str, Any]:
        theme = self.registry.get(theme_id)

        assets = {}

        for role, filename in theme.assets.items():
            path = theme.root / filename
            ready = (
                path.is_file()
                and path.stat().st_size > 0
            )

            assets[role] = {
                "filename": filename,
                "ready": ready,
                "size": (
                    path.stat().st_size
                    if ready
                    else 0
                ),
                "sha256": (
                    sha256(
                        path.read_bytes()
                    ).hexdigest()
                    if ready
                    else None
                ),
            }

        return {
            "theme_id": theme_id,
            "ready": all(
                item["ready"]
                for item in assets.values()
            ),
            "assets": assets,
        }