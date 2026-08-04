from __future__ import annotations

import pytest

from syk_core.runtime_kernel import (
    ModuleHealth,
    ModuleState,
    RuntimeEventBus,
    RuntimeModule,
    RuntimeModuleDescriptor,
    RuntimeModuleManager,
    RuntimeModuleManagerError,
    RuntimeModuleRegistry,
    RuntimeState,
)


class ManagedFakeModule(RuntimeModule):
    def __init__(
        self,
        module_id: str,
        *,
        version: str = "1.0.0",
        dependencies: tuple[str, ...] = tuple(),
        fail_start: bool = False,
        fail_stop: bool = False,
    ) -> None:
        super().__init__(
            RuntimeModuleDescriptor(
                module_id=module_id,
                name=module_id,
                version=version,
                dependencies=dependencies,
            )
        )

        self.fail_start = fail_start
        self.fail_stop = fail_stop
        self.start_count = 0
        self.stop_count = 0

    def start(self) -> None:
        self.start_count += 1

        if self.fail_start:
            raise RuntimeError(
                f"{self.descriptor.module_id} başlatılamadı"
            )

    def stop(self) -> None:
        self.stop_count += 1

        if self.fail_stop:
            raise RuntimeError(
                f"{self.descriptor.module_id} durdurulamadı"
            )


def create_manager() -> RuntimeModuleManager:
    state = RuntimeState.RUNNING

    return RuntimeModuleManager(
        registry=RuntimeModuleRegistry(),
        event_bus=RuntimeEventBus(),
        runtime_state_getter=lambda: state,
    )


def test_factory_register_and_load() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("kamera"),
    )

    module = manager.load("kamera")

    assert module.descriptor.module_id == "kamera"
    assert manager.registry.contains("kamera")
    assert module.state is ModuleState.REGISTERED


def test_duplicate_factory_is_rejected() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("kamera"),
    )

    with pytest.raises(
        RuntimeModuleManagerError,
        match="zaten kayıtlı",
    ):
        manager.register_factory(
            "kamera",
            lambda: ManagedFakeModule("kamera"),
        )


def test_duplicate_module_load_is_rejected() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("kamera"),
    )

    manager.load("kamera")

    with pytest.raises(
        RuntimeModuleManagerError,
        match="zaten yüklü",
    ):
        manager.load("kamera")


def test_factory_module_id_mismatch_is_rejected() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("yanlış"),
    )

    with pytest.raises(
        RuntimeModuleManagerError,
        match="kimliği uyuşmuyor",
    ):
        manager.load("kamera")


def test_enable_auto_starts_dependencies() -> None:
    manager = create_manager()

    manager.register_factory(
        "veri",
        lambda: ManagedFakeModule("veri"),
    )

    manager.register_factory(
        "analiz",
        lambda: ManagedFakeModule(
            "analiz",
            dependencies=("veri",),
        ),
    )

    veri = manager.load("veri")
    analiz = manager.load("analiz")

    manager.enable("analiz")

    assert veri.state is ModuleState.ACTIVE
    assert analiz.state is ModuleState.ACTIVE
    assert veri.health is ModuleHealth.HEALTHY
    assert analiz.health is ModuleHealth.HEALTHY
    assert veri.start_count == 1
    assert analiz.start_count == 1


def test_enable_without_dependency_auto_start_fails() -> None:
    manager = create_manager()

    manager.register_factory(
        "veri",
        lambda: ManagedFakeModule("veri"),
    )

    manager.register_factory(
        "analiz",
        lambda: ManagedFakeModule(
            "analiz",
            dependencies=("veri",),
        ),
    )

    manager.load("veri")
    manager.load("analiz")

    with pytest.raises(
        RuntimeModuleManagerError,
        match="Etkin olmayan bağımlılıklar",
    ):
        manager.enable(
            "analiz",
            auto_start_dependencies=False,
        )


def test_enable_rolls_back_started_dependencies() -> None:
    manager = create_manager()

    manager.register_factory(
        "veri",
        lambda: ManagedFakeModule("veri"),
    )

    manager.register_factory(
        "analiz",
        lambda: ManagedFakeModule(
            "analiz",
            dependencies=("veri",),
            fail_start=True,
        ),
    )

    veri = manager.load("veri")
    analiz = manager.load("analiz")

    with pytest.raises(
        RuntimeModuleManagerError,
        match="etkinleştirilemedi",
    ):
        manager.enable("analiz")

    assert veri.state is ModuleState.STOPPED
    assert veri.stop_count == 1
    assert analiz.state is ModuleState.FAILED
    assert analiz.health is ModuleHealth.UNHEALTHY


def test_disable_protects_active_dependents() -> None:
    manager = create_manager()

    manager.register_factory(
        "veri",
        lambda: ManagedFakeModule("veri"),
    )

    manager.register_factory(
        "analiz",
        lambda: ManagedFakeModule(
            "analiz",
            dependencies=("veri",),
        ),
    )

    manager.load("veri")
    manager.load("analiz")
    manager.enable("analiz")

    with pytest.raises(
        RuntimeModuleManagerError,
        match="Etkin bağımlı modüller",
    ):
        manager.disable("veri")


def test_force_disable_stops_dependents_first() -> None:
    manager = create_manager()

    manager.register_factory(
        "veri",
        lambda: ManagedFakeModule("veri"),
    )

    manager.register_factory(
        "analiz",
        lambda: ManagedFakeModule(
            "analiz",
            dependencies=("veri",),
        ),
    )

    veri = manager.load("veri")
    analiz = manager.load("analiz")

    manager.enable("analiz")
    manager.disable("veri", force=True)

    assert analiz.state is ModuleState.STOPPED
    assert veri.state is ModuleState.STOPPED
    assert analiz.stop_count == 1
    assert veri.stop_count == 1


def test_pause_and_resume_module() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("kamera"),
    )

    module = manager.load("kamera")
    manager.enable("kamera")
    manager.pause("kamera")

    assert module.state is ModuleState.PAUSED

    manager.resume("kamera")

    assert module.state is ModuleState.ACTIVE


def test_restart_stops_and_starts_module() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("kamera"),
    )

    module = manager.load("kamera")
    manager.enable("kamera")
    manager.restart("kamera")

    assert module.state is ModuleState.ACTIVE
    assert module.start_count == 2
    assert module.stop_count == 1


def test_unload_rejects_running_module() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("kamera"),
    )

    manager.load("kamera")
    manager.enable("kamera")

    with pytest.raises(
        RuntimeModuleManagerError,
        match="doğrudan kaldırılamaz",
    ):
        manager.unload("kamera")


def test_force_unload_stops_and_removes_module() -> None:
    manager = create_manager()

    manager.register_factory(
        "kamera",
        lambda: ManagedFakeModule("kamera"),
    )

    module = manager.load("kamera")
    manager.enable("kamera")

    removed = manager.unload(
        "kamera",
        force=True,
    )

    assert removed is module
    assert module.stop_count == 1
    assert not manager.registry.contains("kamera")


def test_reload_replaces_module_and_keeps_active_state() -> None:
    manager = create_manager()
    version = {"value": "1.0.0"}

    def factory() -> ManagedFakeModule:
        return ManagedFakeModule(
            "kamera",
            version=version["value"],
        )

    manager.register_factory(
        "kamera",
        factory,
    )

    old_module = manager.load("kamera")
    manager.enable("kamera")

    version["value"] = "2.0.0"

    new_module = manager.reload("kamera")

    assert new_module is not old_module
    assert new_module.descriptor.version == "2.0.0"
    assert new_module.state is ModuleState.ACTIVE
    assert old_module.stop_count == 1


def test_snapshot_preserves_turkish_keys() -> None:
    manager = create_manager()

    manager.register_factory(
        "görüntü",
        lambda: ManagedFakeModule("görüntü"),
    )

    manager.load("görüntü")
    manager.enable("görüntü")

    payload = manager.snapshot()

    assert payload["çalışma_durumu"] == "çalışıyor"
    assert payload["yüklü_modül_sayısı"] == 1
    assert payload["fabrika_sayısı"] == 1
    assert payload["işlem_sayısı"] >= 3
    assert payload["modüller"][0][
        "module_id"
    ] == "görüntü"


def test_module_operations_are_recorded() -> None:
    manager = create_manager()

    manager.register_factory(
        "harita",
        lambda: ManagedFakeModule("harita"),
    )

    manager.load("harita")
    manager.enable("harita")
    manager.disable("harita")

    operations = manager.operations

    assert operations[-1].operation == "pasifleştirme"
    assert operations[-1].module_id == "harita"
    assert operations[-1].successful is True


def test_runtime_events_are_published() -> None:
    manager = create_manager()

    manager.register_factory(
        "kanıt",
        lambda: ManagedFakeModule("kanıt"),
    )

    manager.load("kanıt")
    manager.enable("kanıt")
    manager.restart("kanıt")
    manager.disable("kanıt")
    manager.unload("kanıt")

    topics = [
        event.topic
        for event in manager.event_bus.history
    ]

    assert "runtime.module.loaded" in topics
    assert "runtime.module.enabled" in topics
    assert "runtime.module.restarted" in topics
    assert "runtime.module.disabled" in topics
    assert "runtime.module.unloaded" in topics
