from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Module:
    module_id: str
    title: str
    hardware_required: bool = False
    runtime_state: str = "hazir"


MODULES = (
    Module("geology", "Jeoloji"),
    Module("frequency", "Frekans"),
    Module("lidar", "LiDAR", True, "donanim_bekliyor"),
    Module("astronomy", "Astronomi"),
    Module("chemical", "Kimyasal Analiz"),
    Module("spectral", "Spektral Analiz", True, "donanim_bekliyor"),
    Module("thermal", "Termal Analiz", True, "donanim_bekliyor"),
    Module("magnetometer", "Manyetometre", True, "donanim_bekliyor"),
    Module("gravimeter", "Gravimetre", True, "donanim_bekliyor"),
    Module("ert", "Elektrik Direnç", True, "donanim_bekliyor"),
    Module("gpr", "GPR", True, "donanim_bekliyor"),
    Module("seismic", "Sismik", True, "donanim_bekliyor"),
    Module("hydro", "Hidrojeoloji"),
    Module("botany", "Botanik"),
    Module("soil", "Toprak"),
    Module("water", "Su"),
)


def list_modules() -> tuple[Module, ...]:
    return MODULES


def get_module(
    module_id: str,
) -> Module:
    for module in MODULES:
        if module.module_id == module_id:
            return module

    raise KeyError(
        module_id
    )
