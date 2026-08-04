"""Dinamik çalışma modülü yönetimi."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from .enums import ModuleHealth, ModuleState, RuntimeState
from .event_bus import RuntimeEvent, RuntimeEventBus
from .module import RuntimeModule
from .registry import (
    RuntimeModuleRegistry,
    RuntimeRegistryError,
)


class RuntimeModuleManagerError(RuntimeError):
    """Dinamik modül yönetim hatası."""


RuntimeModuleFactory = Callable[[], RuntimeModule]


@dataclass(slots=True, frozen=True)
class ModuleOperationRecord:
    operation: str
    module_id: str
    successful: bool
    message: str
    occurred_at: datetime

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "işlem": self.operation,
            "modül_kimliği": self.module_id,
            "başarılı": self.successful,
            "açıklama": self.message,
            "zaman": self.occurred_at.isoformat(),
        }


class RuntimeModuleManager:
    """Modül yükleme, etkinleştirme ve yeniden başlatma motoru."""

    def __init__(
        self,
        *,
        registry: RuntimeModuleRegistry,
        event_bus: RuntimeEventBus,
        runtime_state_getter: Callable[[], RuntimeState],
    ) -> None:
        self.registry = registry
        self.event_bus = event_bus
        self._runtime_state_getter = runtime_state_getter
        self._factories: dict[str, RuntimeModuleFactory] = {}
        self._operations: list[ModuleOperationRecord] = []
        self._lock = RLock()

    def register_factory(
        self,
        module_id: str,
        factory: RuntimeModuleFactory,
    ) -> None:
        normalized_id = module_id.strip()

        if not normalized_id:
            raise ValueError(
                "Modül fabrikası kimliği boş olamaz."
            )

        with self._lock:
            if normalized_id in self._factories:
                raise RuntimeModuleManagerError(
                    "Modül fabrikası zaten kayıtlı: "
                    f"{normalized_id}"
                )

            self._factories[normalized_id] = factory

        self._record(
            operation="fabrika_kaydı",
            module_id=normalized_id,
            successful=True,
            message="Modül fabrikası kaydedildi.",
        )

    def unregister_factory(
        self,
        module_id: str,
    ) -> None:
        with self._lock:
            if module_id not in self._factories:
                raise RuntimeModuleManagerError(
                    "Modül fabrikası bulunamadı: "
                    f"{module_id}"
                )

            del self._factories[module_id]

        self._record(
            operation="fabrika_silme",
            module_id=module_id,
            successful=True,
            message="Modül fabrikası kaldırıldı.",
        )

    def load(
        self,
        module_id: str,
    ) -> RuntimeModule:
        with self._lock:
            if self.registry.contains(module_id):
                raise RuntimeModuleManagerError(
                    f"Modül zaten yüklü: {module_id}"
                )

            factory = self._factories.get(module_id)

        if factory is None:
            raise RuntimeModuleManagerError(
                f"Modül fabrikası bulunamadı: {module_id}"
            )

        try:
            module = factory()
        except Exception as exc:
            self._record(
                operation="yükleme",
                module_id=module_id,
                successful=False,
                message=str(exc),
            )

            raise RuntimeModuleManagerError(
                f"Modül üretilemedi: {module_id}: {exc}"
            ) from exc

        if module.descriptor.module_id != module_id:
            message = (
                "Fabrika modül kimliği uyuşmuyor: "
                f"beklenen={module_id}, "
                f"gelen={module.descriptor.module_id}"
            )

            self._record(
                operation="yükleme",
                module_id=module_id,
                successful=False,
                message=message,
            )

            raise RuntimeModuleManagerError(message)

        self.registry.register(module)

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.module.loaded",
                source="runtime_module_manager",
                payload={
                    "module_id": module_id,
                    "version": module.descriptor.version,
                },
            )
        )

        self._record(
            operation="yükleme",
            module_id=module_id,
            successful=True,
            message="Modül yüklendi.",
        )

        return module

    def unload(
        self,
        module_id: str,
        *,
        force: bool = False,
    ) -> RuntimeModule:
        module = self._get_module(module_id)

        dependents = self._find_dependents(module_id)

        if dependents and not force:
            raise RuntimeModuleManagerError(
                "Modül başka modüller tarafından kullanılıyor: "
                f"{module_id} <- {', '.join(dependents)}"
            )

        if module.state in {
            ModuleState.ACTIVE,
            ModuleState.PAUSED,
            ModuleState.STARTING,
            ModuleState.STOPPING,
        }:
            if not force:
                raise RuntimeModuleManagerError(
                    "Çalışan modül doğrudan kaldırılamaz: "
                    f"{module_id}"
                )

            self.disable(module_id, force=True)

        removed = self.registry.unregister(module_id)

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.module.unloaded",
                source="runtime_module_manager",
                payload={
                    "module_id": module_id,
                    "forced": force,
                },
            )
        )

        self._record(
            operation="kaldırma",
            module_id=module_id,
            successful=True,
            message="Modül kaldırıldı.",
        )

        return removed

    def enable(
        self,
        module_id: str,
        *,
        auto_start_dependencies: bool = True,
    ) -> RuntimeModule:
        module = self._get_module(module_id)

        if module.state is ModuleState.ACTIVE:
            return module

        if module.state is ModuleState.PAUSED:
            module.resume()

            self._publish_state_event(
                topic="runtime.module.resumed",
                module=module,
            )

            self._record(
                operation="etkinleştirme",
                module_id=module_id,
                successful=True,
                message="Bekleyen modül devam ettirildi.",
            )

            return module

        order = self.registry.resolve_start_order(
            (module_id,)
        )

        if not auto_start_dependencies:
            inactive_dependencies = [
                dependency_id
                for dependency_id in module.descriptor.dependencies
                if self.registry.get(
                    dependency_id
                ).state is not ModuleState.ACTIVE
            ]

            if inactive_dependencies:
                raise RuntimeModuleManagerError(
                    "Etkin olmayan bağımlılıklar var: "
                    + ", ".join(inactive_dependencies)
                )

            order = (module_id,)

        started: list[str] = []

        try:
            for current_id in order:
                current = self.registry.get(current_id)

                if current.state is ModuleState.ACTIVE:
                    continue

                if current.state is ModuleState.PAUSED:
                    current.resume()
                    started.append(current_id)
                    continue

                current.state = ModuleState.STARTING

                try:
                    current.start()
                except Exception:
                    current.state = ModuleState.FAILED
                    current.health = ModuleHealth.UNHEALTHY
                    raise

                current.state = ModuleState.ACTIVE
                current.health = ModuleHealth.HEALTHY
                current.last_error = None
                started.append(current_id)

                self._publish_state_event(
                    topic="runtime.module.enabled",
                    module=current,
                )

                self._record(
                    operation="etkinleştirme",
                    module_id=current_id,
                    successful=True,
                    message="Modül etkinleştirildi.",
                )

        except Exception as exc:
            self._rollback_enabled_modules(started)

            self._record(
                operation="etkinleştirme",
                module_id=module_id,
                successful=False,
                message=str(exc),
            )

            raise RuntimeModuleManagerError(
                f"Modül etkinleştirilemedi: {module_id}: {exc}"
            ) from exc

        return module

    def disable(
        self,
        module_id: str,
        *,
        force: bool = False,
    ) -> RuntimeModule:
        module = self._get_module(module_id)

        if module.state in {
            ModuleState.REGISTERED,
            ModuleState.STOPPED,
        }:
            module.state = ModuleState.STOPPED
            return module

        dependents = [
            dependent_id
            for dependent_id in self._find_dependents(module_id)
            if self.registry.get(
                dependent_id
            ).state in {
                ModuleState.ACTIVE,
                ModuleState.PAUSED,
            }
        ]

        if dependents and not force:
            raise RuntimeModuleManagerError(
                "Etkin bağımlı modüller varken "
                "modül durdurulamaz: "
                f"{module_id} <- {', '.join(dependents)}"
            )

        if force:
            for dependent_id in reversed(dependents):
                self.disable(
                    dependent_id,
                    force=True,
                )

        module.state = ModuleState.STOPPING

        try:
            module.stop()
        except Exception as exc:
            module.state = ModuleState.FAILED
            module.health = ModuleHealth.UNHEALTHY
            module.last_error = str(exc)

            self._record(
                operation="pasifleştirme",
                module_id=module_id,
                successful=False,
                message=str(exc),
            )

            raise RuntimeModuleManagerError(
                f"Modül durdurulamadı: {module_id}: {exc}"
            ) from exc

        module.state = ModuleState.STOPPED
        module.health = ModuleHealth.UNKNOWN
        module.last_error = None

        self._publish_state_event(
            topic="runtime.module.disabled",
            module=module,
        )

        self._record(
            operation="pasifleştirme",
            module_id=module_id,
            successful=True,
            message="Modül pasifleştirildi.",
        )

        return module

    def pause(
        self,
        module_id: str,
    ) -> RuntimeModule:
        module = self._get_module(module_id)
        module.pause()

        self._publish_state_event(
            topic="runtime.module.paused",
            module=module,
        )

        self._record(
            operation="bekletme",
            module_id=module_id,
            successful=True,
            message="Modül beklemeye alındı.",
        )

        return module

    def resume(
        self,
        module_id: str,
    ) -> RuntimeModule:
        module = self._get_module(module_id)
        module.resume()

        self._publish_state_event(
            topic="runtime.module.resumed",
            module=module,
        )

        self._record(
            operation="devam",
            module_id=module_id,
            successful=True,
            message="Modül çalışmaya devam etti.",
        )

        return module

    def restart(
        self,
        module_id: str,
    ) -> RuntimeModule:
        module = self._get_module(module_id)

        if module.state in {
            ModuleState.ACTIVE,
            ModuleState.PAUSED,
            ModuleState.FAILED,
        }:
            self.disable(
                module_id,
                force=False,
            )

        module = self.enable(module_id)

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.module.restarted",
                source="runtime_module_manager",
                payload={
                    "module_id": module_id,
                },
            )
        )

        self._record(
            operation="yeniden_başlatma",
            module_id=module_id,
            successful=True,
            message="Modül yeniden başlatıldı.",
        )

        return module

    def reload(
        self,
        module_id: str,
    ) -> RuntimeModule:
        previous = self._get_module(module_id)
        previous_state = previous.state

        dependents = self._find_dependents(module_id)

        active_dependents = [
            dependent_id
            for dependent_id in dependents
            if self.registry.get(
                dependent_id
            ).state in {
                ModuleState.ACTIVE,
                ModuleState.PAUSED,
            }
        ]

        if active_dependents:
            raise RuntimeModuleManagerError(
                "Etkin bağımlılar nedeniyle modül "
                "yeniden yüklenemiyor: "
                + ", ".join(active_dependents)
            )

        if previous_state in {
            ModuleState.ACTIVE,
            ModuleState.PAUSED,
            ModuleState.FAILED,
        }:
            self.disable(
                module_id,
                force=False,
            )

        self.registry.unregister(module_id)

        try:
            replacement = self.load(module_id)

            if previous_state in {
                ModuleState.ACTIVE,
                ModuleState.PAUSED,
            }:
                self.enable(module_id)

                if previous_state is ModuleState.PAUSED:
                    self.pause(module_id)

        except Exception as exc:
            if not self.registry.contains(module_id):
                self.registry.register(previous)

            raise RuntimeModuleManagerError(
                f"Modül yeniden yüklenemedi: "
                f"{module_id}: {exc}"
            ) from exc

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.module.reloaded",
                source="runtime_module_manager",
                payload={
                    "module_id": module_id,
                    "previous_version": (
                        previous.descriptor.version
                    ),
                    "new_version": (
                        replacement.descriptor.version
                    ),
                },
            )
        )

        self._record(
            operation="yeniden_yükleme",
            module_id=module_id,
            successful=True,
            message="Modül yeniden yüklendi.",
        )

        return replacement

    def module_snapshot(
        self,
        module_id: str,
    ) -> dict[str, Any]:
        return self._get_module(module_id).snapshot()

    def snapshot(self) -> dict[str, Any]:
        modules = self.registry.snapshot()

        return {
            "çalışma_durumu": (
                self._runtime_state_getter().value
            ),
            "yüklü_modül_sayısı": len(modules),
            "fabrika_sayısı": len(self._factories),
            "işlem_sayısı": len(self._operations),
            "modüller": modules,
            "işlemler": [
                operation.to_runtime_dict()
                for operation in self._operations
            ],
        }

    @property
    def operations(
        self,
    ) -> tuple[ModuleOperationRecord, ...]:
        with self._lock:
            return tuple(self._operations)

    def _get_module(
        self,
        module_id: str,
    ) -> RuntimeModule:
        try:
            return self.registry.get(module_id)
        except RuntimeRegistryError as exc:
            raise RuntimeModuleManagerError(
                str(exc)
            ) from exc

    def _find_dependents(
        self,
        module_id: str,
    ) -> list[str]:
        return sorted(
            module.descriptor.module_id
            for module in self.registry.list_modules()
            if module_id
            in module.descriptor.dependencies
        )

    def _publish_state_event(
        self,
        *,
        topic: str,
        module: RuntimeModule,
    ) -> None:
        self.event_bus.publish(
            RuntimeEvent(
                topic=topic,
                source="runtime_module_manager",
                payload={
                    "module_id": (
                        module.descriptor.module_id
                    ),
                    "state": module.state.value,
                    "health": module.health.value,
                },
            )
        )

    def _rollback_enabled_modules(
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

    def _record(
        self,
        *,
        operation: str,
        module_id: str,
        successful: bool,
        message: str,
    ) -> None:
        record = ModuleOperationRecord(
            operation=operation,
            module_id=module_id,
            successful=successful,
            message=message,
            occurred_at=datetime.now(UTC),
        )

        with self._lock:
            self._operations.append(record)
