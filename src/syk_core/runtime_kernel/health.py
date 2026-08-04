"""Çalışma çekirdeği sağlık modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .enums import ModuleHealth, ModuleState, RuntimeState


@dataclass(slots=True, frozen=True)
class ModuleHealthReport:
    module_id: str
    state: ModuleState
    health: ModuleHealth
    last_error: str | None = None

    @property
    def is_operational(self) -> bool:
        return (
            self.state
            in {
                ModuleState.ACTIVE,
                ModuleState.PAUSED,
            }
            and self.health
            in {
                ModuleHealth.HEALTHY,
                ModuleHealth.DEGRADED,
            }
        )


@dataclass(slots=True, frozen=True)
class RuntimeHealthReport:
    runtime_state: RuntimeState
    modules: tuple[
        ModuleHealthReport,
        ...,
    ]
    event_count: int
    handler_error_count: int
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def healthy_module_count(self) -> int:
        return sum(
            1
            for module in self.modules
            if module.health is ModuleHealth.HEALTHY
        )

    @property
    def failed_module_count(self) -> int:
        return sum(
            1
            for module in self.modules
            if module.state is ModuleState.FAILED
            or module.health is ModuleHealth.UNHEALTHY
        )

    @property
    def is_healthy(self) -> bool:
        return (
            self.runtime_state is RuntimeState.RUNNING
            and self.failed_module_count == 0
            and self.handler_error_count == 0
        )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "çalışma_durumu": self.runtime_state.value,
            "sağlıklı": self.is_healthy,
            "sağlıklı_modül_sayısı": (
                self.healthy_module_count
            ),
            "hatalı_modül_sayısı": (
                self.failed_module_count
            ),
            "olay_sayısı": self.event_count,
            "olay_işleyici_hatası": (
                self.handler_error_count
            ),
            "modüller": [
                {
                    "modül_kimliği": module.module_id,
                    "durum": module.state.value,
                    "sağlık": module.health.value,
                    "son_hata": module.last_error,
                    "çalışabilir": module.is_operational,
                }
                for module in self.modules
            ],
            "üretilme_zamanı": (
                self.generated_at.isoformat()
            ),
        }
