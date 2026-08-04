from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class ThemeRuntimeProtocol(Protocol):
    def set(
        self,
        theme_id: str,
    ) -> dict[str, Any]:
        ...

    def automatic(
        self,
        *,
        hour: int,
        weather: str,
        device: str,
    ) -> dict[str, Any]:
        ...

    def snapshot(
        self,
    ) -> dict[str, Any]:
        ...


class EnvironmentProtocol(Protocol):
    def current(
        self,
    ) -> dict[str, Any]:
        ...


@dataclass(slots=True)
class JarminSystemAdapters:
    theme_runtime: (
        ThemeRuntimeProtocol | None
    ) = None

    environment: (
        EnvironmentProtocol | None
    ) = None

    def theme_change(
        self,
        entities: dict[str, Any],
    ) -> dict[str, Any]:
        theme_id = entities.get(
            "theme_id"
        )

        if not theme_id:
            raise ValueError(
                "Tema tercihi belirtilmedi."
            )

        if self.theme_runtime is None:
            return {
                "message": (
                    "Tema değiştirme isteği "
                    "kaydedildi."
                ),
                "action": "theme_change",
                "theme_id": theme_id,
                "applied": False,
            }

        if theme_id == "automatic":
            environment = (
                self.environment.current()
                if self.environment
                is not None
                else {
                    "hour": 12,
                    "weather": "clear",
                }
            )

            result = (
                self.theme_runtime
                .automatic(
                    hour=int(
                        environment.get(
                            "hour",
                            12,
                        )
                    ),
                    weather=str(
                        environment.get(
                            "weather",
                            "clear",
                        )
                    ),
                    device="desktop",
                )
            )

        else:
            result = (
                self.theme_runtime.set(
                    theme_id
                )
            )

        return {
            "message": (
                "Tema başarıyla değiştirildi."
            ),
            "action": "theme_change",
            "theme_id": theme_id,
            "applied": True,
            "runtime": result,
        }

    def system_status(
        self,
        entities: dict[str, Any],
    ) -> dict[str, Any]:
        theme = (
            self.theme_runtime.snapshot()
            if self.theme_runtime
            is not None
            else None
        )

        environment = (
            self.environment.current()
            if self.environment
            is not None
            else None
        )

        return {
            "message": (
                "SyKaşif çalışma durumu "
                "hazırlandı."
            ),
            "action": "system_status",
            "theme": theme,
            "environment": environment,
            "entities": entities,
        }