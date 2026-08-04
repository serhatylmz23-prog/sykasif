"""SyKaşif gerçek çalışma çekirdeği."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from .enums import (
    ModuleHealth,
    ModuleState,
    RuntimeState,
)
from .event_bus import RuntimeEvent, RuntimeEventBus
from .health import (
    ModuleHealthReport,
    RuntimeHealthReport,
)
from .module import RuntimeModule
from .registry import RuntimeModuleRegistry


class RuntimeKernelError(RuntimeError):
    """Çalışma çekirdeği hatası."""


@dataclass(slots=True, frozen=True)
class RuntimeKernelSnapshot:
    state: RuntimeState
    module_count: int
    active_module_count: int
    event_count: int
    generated_at: datetime
    modules: tuple[dict[str, Any], ...]

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "durum": self.state.value,
            "modül_sayısı": self.module_count,
            "aktif_modül_sayısı": (
                self.active_module_count
            ),
            "olay_sayısı": self.event_count,
            "üretilme_zamanı": (
                self.generated_at.isoformat()
            ),
            "modüller": list(self.modules),
        }


class RuntimeKernel:
    def __init__(
        self,
        *,
        registry: RuntimeModuleRegistry | None = None,
        event_bus: RuntimeEventBus | None = None,
    ) -> None:
        self.registry = (
            registry or RuntimeModuleRegistry()
        )
        self.event_bus = (
            event_bus or RuntimeEventBus()
        )
        self.state = RuntimeState.CREATED
        self._lock = RLock()

    def register_module(
        self,
        module: RuntimeModule,
    ) -> None:
        with self._lock:
            if self.state not in {
                RuntimeState.CREATED,
                RuntimeState.STOPPED,
            }:
                raise RuntimeKernelError(
                    "Çalışan çekirdeğe doğrudan "
                    "modül kaydı yapılamaz."
                )

            self.registry.register(module)

    def start(
        self,
        module_ids: tuple[str, ...] | None = None,
    ) -> None:
        with self._lock:
            if self.state is RuntimeState.RUNNING:
                return

            if self.state is RuntimeState.STARTING:
                raise RuntimeKernelError(
                    "Çekirdek zaten başlatılıyor."
                )

            self.state = RuntimeState.STARTING

        started_module_ids: list[str] = []

        try:
            start_order = (
                self.registry.resolve_start_order(
                    module_ids
                )
            )

            for module_id in start_order:
                module = self.registry.get(module_id)
                module.state = ModuleState.STARTING

                try:
                    module.start()
                    module.state = ModuleState.ACTIVE
                    module.health = ModuleHealth.HEALTHY
                    module.last_error = None
                    started_module_ids.append(module_id)

                    self.event_bus.publish(
                        RuntimeEvent(
                            topic="runtime.module.started",
                            source="runtime_kernel",
                            payload={
                                "module_id": module_id,
                            },
                        )
                    )
                except Exception as exc:
                    module.state = ModuleState.FAILED
                    module.health = ModuleHealth.UNHEALTHY
                    module.last_error = str(exc)
                    raise

            with self._lock:
                self.state = RuntimeState.RUNNING

            self.event_bus.publish(
                RuntimeEvent(
                    topic="runtime.started",
                    source="runtime_kernel",
                    payload={
                        "modules": started_module_ids,
                    },
                )
            )

        except Exception as exc:
            self._rollback_started_modules(
                started_module_ids
            )

            with self._lock:
                self.state = RuntimeState.FAILED

            raise RuntimeKernelError(
                f"Çalışma çekirdeği başlatılamadı: {exc}"
            ) from exc

    def stop(self) -> None:
        with self._lock:
            if self.state in {
                RuntimeState.CREATED,
                RuntimeState.STOPPED,
            }:
                self.state = RuntimeState.STOPPED
                return

            self.state = RuntimeState.STOPPING

        stop_errors: list[str] = []

        modules = list(
            self.registry.list_modules()
        )

        for module in reversed(modules):
            if module.state not in {
                ModuleState.ACTIVE,
                ModuleState.PAUSED,
                ModuleState.FAILED,
            }:
                continue

            module.state = ModuleState.STOPPING

            try:
                module.stop()
                module.state = ModuleState.STOPPED
                module.health = ModuleHealth.UNKNOWN
            except Exception as exc:
                module.state = ModuleState.FAILED
                module.health = ModuleHealth.UNHEALTHY
                module.last_error = str(exc)
                stop_errors.append(
                    f"{module.descriptor.module_id}: {exc}"
                )

        with self._lock:
            self.state = (
                RuntimeState.FAILED
                if stop_errors
                else RuntimeState.STOPPED
            )

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.stopped",
                source="runtime_kernel",
                payload={
                    "errors": stop_errors,
                },
            )
        )

        if stop_errors:
            raise RuntimeKernelError(
                "Modül durdurma hataları: "
                + " | ".join(stop_errors)
            )

    def pause_module(
        self,
        module_id: str,
    ) -> None:
        module = self.registry.get(module_id)
        module.pause()

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.module.paused",
                source="runtime_kernel",
                payload={"module_id": module_id},
            )
        )

    def resume_module(
        self,
        module_id: str,
    ) -> None:
        module = self.registry.get(module_id)
        module.resume()

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.module.resumed",
                source="runtime_kernel",
                payload={"module_id": module_id},
            )
        )

    def health_report(self) -> RuntimeHealthReport:
        module_reports = tuple(
            ModuleHealthReport(
                module_id=module.descriptor.module_id,
                state=module.state,
                health=module.health_check(),
                last_error=module.last_error,
            )
            for module in self.registry.list_modules()
        )

        event_snapshot = self.event_bus.snapshot()

        return RuntimeHealthReport(
            runtime_state=self.state,
            modules=module_reports,
            event_count=int(
                event_snapshot["event_count"]
            ),
            handler_error_count=int(
                event_snapshot[
                    "handler_error_count"
                ]
            ),
        )

    def snapshot(self) -> RuntimeKernelSnapshot:
        modules = tuple(
            self.registry.snapshot()
        )

        return RuntimeKernelSnapshot(
            state=self.state,
            module_count=len(modules),
            active_module_count=sum(
                1
                for module in modules
                if module["state"]
                == ModuleState.ACTIVE.value
            ),
            event_count=len(
                self.event_bus.history
            ),
            generated_at=datetime.now(UTC),
            modules=modules,
        )

    def _rollback_started_modules(
        self,
        module_ids: list[str],
    ) -> None:
        for module_id in reversed(module_ids):
            module = self.registry.get(module_id)

            try:
                module.stop()
                module.state = ModuleState.STOPPED
                module.health = ModuleHealth.UNKNOWN
            except Exception as exc:
                module.state = ModuleState.FAILED
                module.health = ModuleHealth.UNHEALTHY
                module.last_error = str(exc)
