from __future__ import annotations


class AdaptiveThemeResolver:
    def resolve(
        self,
        *,
        hour: int,
        weather: str,
        device: str = "desktop",
        preferred: str | None = None,
    ) -> str:
        if preferred in {
            "gold",
            "silver",
            "dark",
        }:
            return preferred

        if device == "mobile":
            return "mobile"

        if device == "tablet":
            return "tablet"

        if weather in {
            "storm",
            "fog",
        }:
            return "dark"

        if hour < 7 or hour >= 19:
            return "silver"

        return "gold"