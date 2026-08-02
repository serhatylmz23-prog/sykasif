"""
SPR-003-UI-0004
SyKaşif Runtime Manager
"""

from .module_registry import MODULES


class RuntimeManager:

    def __init__(self):
        self._modules = {m.id: m for m in MODULES}
        self._active = "dashboard"

    @property
    def active(self):
        return self._modules[self._active]

    def activate(self, module_id: str):

        if module_id not in self._modules:
            raise KeyError(f"Module not found: {module_id}")

        self._active = module_id
        return self.active

    def modules(self):
        return list(self._modules.values())

    def exists(self, module_id: str) -> bool:
        return module_id in self._modules
