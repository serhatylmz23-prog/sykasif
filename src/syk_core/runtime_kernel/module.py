"""Çalışma çekirdeği modül sözleşmesi."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .enums import ModuleHealth, ModuleState


class RuntimeModuleError(RuntimeError):
    """Çalışma modülü hatası."""


@dataclass(slots=True, frozen=True)
class RuntimeModuleDescriptor:
    module_id: str
    name: str
    version: str
    dependencies: tuple[str, ...] = tuple()
    capabilities: tuple[str, ...] = tuple()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.module_id.strip():
            raise ValueError("Modül kimliği boş olamaz.")

        if not self.name.strip():
            raise ValueError("Modül adı boş olamaz.")

        if not self.version.strip():
            raise ValueError("Modül sürümü boş olamaz.")

        if self.module_id in self.dependencies:
            raise ValueError(
                "Modül kendi kendisine bağımlı olamaz."
            )


class RuntimeModule(ABC):
    """Tüm çalışma modüllerinin uygulayacağı temel sözleşme."""

    def __init__(
        self,
        descriptor: RuntimeModuleDescriptor,
    ) -> None:
        self.descriptor = descriptor
        self.state = ModuleState.REGISTERED
        self.health = ModuleHealth.UNKNOWN
        self.last_error: str | None = None

    @abstractmethod
    def start(self) -> None:
        """Modülü başlat."""

    @abstractmethod
    def stop(self) -> None:
        """Modülü durdur."""

    def pause(self) -> None:
        if self.state is not ModuleState.ACTIVE:
            raise RuntimeModuleError(
                "Yalnız aktif modül beklemeye alınabilir."
            )

        self.state = ModuleState.PAUSED

    def resume(self) -> None:
        if self.state is not ModuleState.PAUSED:
            raise RuntimeModuleError(
                "Yalnız bekleyen modül devam ettirilebilir."
            )

        self.state = ModuleState.ACTIVE

    def health_check(self) -> ModuleHealth:
        return self.health

    def snapshot(self) -> dict[str, Any]:
        return {
            "module_id": self.descriptor.module_id,
            "name": self.descriptor.name,
            "version": self.descriptor.version,
            "dependencies": list(
                self.descriptor.dependencies
            ),
            "capabilities": list(
                self.descriptor.capabilities
            ),
            "state": self.state.value,
            "health": self.health.value,
            "last_error": self.last_error,
            "metadata": dict(
                self.descriptor.metadata
            ),
        }
