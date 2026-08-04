from __future__ import annotations

import pytest

from syk_core.runtime_kernel import (
    ModuleHealth,
    ModuleState,
    RuntimeEvent,
    RuntimeEventBus,
    RuntimeKernel,
    RuntimeKernelError,
    RuntimeModule,
    RuntimeModuleDescriptor,
    RuntimeModuleRegistry,
    RuntimeRegistryError,
    RuntimeState,
)


class FakeModule(RuntimeModule):
    def __init__(
        self,
        module_id: str,
        *,
        dependencies: tuple[str, ...] = tuple(),
        fail_start: bool = False,
        fail_stop: bool = False,
    ) -> None:
        super().__init__(
            RuntimeModuleDescriptor(
                module_id=module_id,
                name=module_id,
                version="1.0.0",
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


def test_registry_resolves_dependency_order() -> None:
    registry = RuntimeModuleRegistry()

    registry.register(
        FakeModule("veri")
    )
    registry.register(
        FakeModule(
            "analiz",
            dependencies=("veri",),
        )
    )
    registry.register(
        FakeModule(
            "rapor",
            dependencies=("analiz",),
        )
    )

    assert registry.resolve_start_order(
        ("rapor",)
    ) == (
        "veri",
        "analiz",
        "rapor",
    )


def test_registry_detects_missing_dependency() -> None:
    registry = RuntimeModuleRegistry()

    registry.register(
        FakeModule(
            "analiz",
            dependencies=("olmayan",),
        )
    )

    with pytest.raises(
        RuntimeRegistryError,
        match="Eksik bağımlılık",
    ):
        registry.resolve_start_order()


def test_registry_detects_dependency_cycle() -> None:
    registry = RuntimeModuleRegistry()

    registry.register(
        FakeModule(
            "bir",
            dependencies=("iki",),
        )
    )
    registry.register(
        FakeModule(
            "iki",
            dependencies=("bir",),
        )
    )

    with pytest.raises(
        RuntimeRegistryError,
        match="Döngüsel",
    ):
        registry.resolve_start_order()


def test_event_bus_delivers_topic_and_wildcard() -> None:
    bus = RuntimeEventBus()
    received: list[str] = []

    bus.subscribe(
        "runtime.started",
        lambda event: received.append(
            f"özel:{event.topic}"
        ),
    )
    bus.subscribe(
        "*",
        lambda event: received.append(
            f"genel:{event.topic}"
        ),
    )

    handled = bus.publish(
        RuntimeEvent(
            topic="runtime.started",
            source="test",
        )
    )

    assert handled == 2
    assert received == [
        "özel:runtime.started",
        "genel:runtime.started",
    ]
    assert len(bus.history) == 1


def test_kernel_starts_modules_in_dependency_order() -> None:
    registry = RuntimeModuleRegistry()

    veri = FakeModule("veri")
    analiz = FakeModule(
        "analiz",
        dependencies=("veri",),
    )

    registry.register(veri)
    registry.register(analiz)

    kernel = RuntimeKernel(
        registry=registry
    )

    kernel.start(("analiz",))

    assert kernel.state is RuntimeState.RUNNING
    assert veri.state is ModuleState.ACTIVE
    assert analiz.state is ModuleState.ACTIVE
    assert veri.health is ModuleHealth.HEALTHY
    assert analiz.health is ModuleHealth.HEALTHY
    assert veri.start_count == 1
    assert analiz.start_count == 1


def test_kernel_rolls_back_when_module_fails() -> None:
    registry = RuntimeModuleRegistry()

    veri = FakeModule("veri")
    analiz = FakeModule(
        "analiz",
        dependencies=("veri",),
        fail_start=True,
    )

    registry.register(veri)
    registry.register(analiz)

    kernel = RuntimeKernel(
        registry=registry
    )

    with pytest.raises(
        RuntimeKernelError,
        match="başlatılamadı",
    ):
        kernel.start(("analiz",))

    assert kernel.state is RuntimeState.FAILED
    assert veri.state is ModuleState.STOPPED
    assert veri.stop_count == 1
    assert analiz.state is ModuleState.FAILED
    assert analiz.health is ModuleHealth.UNHEALTHY


def test_kernel_pause_resume_and_stop() -> None:
    module = FakeModule("kamera")
    kernel = RuntimeKernel()
    kernel.register_module(module)

    kernel.start()
    kernel.pause_module("kamera")

    assert module.state is ModuleState.PAUSED

    kernel.resume_module("kamera")

    assert module.state is ModuleState.ACTIVE

    kernel.stop()

    assert kernel.state is RuntimeState.STOPPED
    assert module.state is ModuleState.STOPPED
    assert module.stop_count == 1


def test_kernel_health_report_is_turkish_safe() -> None:
    module = FakeModule("görüntü_analizi")
    kernel = RuntimeKernel()
    kernel.register_module(module)
    kernel.start()

    payload = kernel.health_report().to_runtime_dict()

    assert payload["çalışma_durumu"] == "çalışıyor"
    assert payload["sağlıklı"] is True
    assert payload["sağlıklı_modül_sayısı"] == 1
    assert payload["modüller"][0][
        "modül_kimliği"
    ] == "görüntü_analizi"


def test_kernel_snapshot_reports_active_modules() -> None:
    kernel = RuntimeKernel()
    kernel.register_module(
        FakeModule("harita")
    )
    kernel.register_module(
        FakeModule("kanıt")
    )

    kernel.start()

    snapshot = kernel.snapshot()

    assert snapshot.module_count == 2
    assert snapshot.active_module_count == 2
    assert snapshot.event_count == 3
    assert snapshot.to_runtime_dict()[
        "aktif_modül_sayısı"
    ] == 2
