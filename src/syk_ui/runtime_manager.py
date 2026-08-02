from .module_registry import MODULES, Module


class RuntimeManager:
    def __init__(self):
        self._modules = {module.id: module for module in MODULES}
        self._active = "dashboard"

    @property
    def active(self) -> Module:
        return self._modules[self._active]

    def activate(self, module_id: str) -> Module:
        if module_id not in self._modules:
            raise KeyError(f"Module not found: {module_id}")

        self._active = module_id
        return self.active

    def modules(self) -> list[Module]:
        return list(self._modules.values())

    def exists(self, module_id: str) -> bool:
        return module_id in self._modules
