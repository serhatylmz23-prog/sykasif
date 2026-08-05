from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TerminalModule:
    key: str
    label: str
    visible: bool = True
    enabled: bool = True
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TerminalState:
    terminal_id: str
    device_type: str
    user_id: str
    role: str
    status: str = "ready"
    connected: bool = True
    active_project_id: str | None = None
    modules: list[TerminalModule] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "terminal_id": self.terminal_id,
            "device_type": self.device_type,
            "user_id": self.user_id,
            "role": self.role,
            "status": self.status,
            "connected": self.connected,
            "active_project_id": self.active_project_id,
            "modules": [
                module.to_dict()
                for module in sorted(
                    self.modules,
                    key=lambda item: item.order,
                )
            ],
        }


def default_terminal_state() -> TerminalState:
    return TerminalState(
        terminal_id="syk-main-terminal",
        device_type="desktop",
        user_id="local-user",
        role="founder",
        modules=[
            TerminalModule("projects", "Projeler", order=10),
            TerminalModule("research", "Araştırmalar", order=20),
            TerminalModule("kasif", "Kaşif", order=30),
            TerminalModule("map", "Harita", order=40),
            TerminalModule("evidence", "Kanıt", order=50),
            TerminalModule("reports", "Raporlar", order=60),
            TerminalModule("devices", "Cihazlar", order=70),
            TerminalModule("notifications", "Bildirimler", order=80),
            TerminalModule("institute", "Enstitü Merkezi", order=90),
        ],
    )