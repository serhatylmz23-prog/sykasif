"""Çalışma modülü kayıt merkezi."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .module import RuntimeModule


class RuntimeRegistryError(RuntimeError):
    """Çalışma kayıt merkezi hatası."""


class RuntimeModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, RuntimeModule] = {}

    def register(
        self,
        module: RuntimeModule,
    ) -> None:
        module_id = module.descriptor.module_id

        if module_id in self._modules:
            raise RuntimeRegistryError(
                f"Modül zaten kayıtlı: {module_id}"
            )

        self._modules[module_id] = module

    def unregister(
        self,
        module_id: str,
    ) -> RuntimeModule:
        try:
            return self._modules.pop(module_id)
        except KeyError as exc:
            raise RuntimeRegistryError(
                f"Modül bulunamadı: {module_id}"
            ) from exc

    def get(
        self,
        module_id: str,
    ) -> RuntimeModule:
        try:
            return self._modules[module_id]
        except KeyError as exc:
            raise RuntimeRegistryError(
                f"Modül bulunamadı: {module_id}"
            ) from exc

    def contains(
        self,
        module_id: str,
    ) -> bool:
        return module_id in self._modules

    def list_modules(
        self,
    ) -> tuple[RuntimeModule, ...]:
        return tuple(
            self._modules[module_id]
            for module_id in sorted(self._modules)
        )

    def resolve_start_order(
        self,
        selected_module_ids: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        selected = (
            set(selected_module_ids)
            if selected_module_ids is not None
            else set(self._modules)
        )

        for module_id in selected:
            if module_id not in self._modules:
                raise RuntimeRegistryError(
                    f"Başlatılacak modül kayıtlı değil: {module_id}"
                )

        dependency_graph: dict[str, set[str]] = defaultdict(set)

        pending = list(selected)

        while pending:
            module_id = pending.pop()
            module = self._modules[module_id]

            for dependency_id in module.descriptor.dependencies:
                if dependency_id not in self._modules:
                    raise RuntimeRegistryError(
                        f"Eksik bağımlılık: "
                        f"{module_id} -> {dependency_id}"
                    )

                dependency_graph[module_id].add(
                    dependency_id
                )

                if dependency_id not in selected:
                    selected.add(dependency_id)
                    pending.append(dependency_id)

        ordered: list[str] = []
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(module_id: str) -> None:
            if module_id in permanent:
                return

            if module_id in temporary:
                raise RuntimeRegistryError(
                    "Döngüsel modül bağımlılığı bulundu."
                )

            temporary.add(module_id)

            for dependency_id in sorted(
                dependency_graph[module_id]
            ):
                visit(dependency_id)

            temporary.remove(module_id)
            permanent.add(module_id)
            ordered.append(module_id)

        for module_id in sorted(selected):
            visit(module_id)

        return tuple(ordered)

    def snapshot(self) -> list[dict[str, object]]:
        return [
            module.snapshot()
            for module in self.list_modules()
        ]
