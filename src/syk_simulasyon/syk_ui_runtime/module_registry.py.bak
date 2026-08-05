from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

ASSETS = {
    "css": STATIC / "css",
    "js": STATIC / "js",
    "images": STATIC / "images",
    "icons": STATIC / "icons",
    "audio": STATIC / "audio",
}


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    enabled: bool = True


MODULES = [
    Module("dashboard", "Ana Terminal"),
    Module("syframe", "SyFrame"),
    Module("maps", "Haritalar"),
    Module("geology", "Jeoloji"),
    Module("sonar", "Sonar"),
    Module("frequency", "Frekans"),
    Module("material", "Materyal"),
    Module("measurement", "Ölçüm"),
    Module("gps", "GPS"),
    Module("rtk", "RTK"),
    Module("lidar", "LiDAR"),
    Module("history", "Tarih"),
    Module("archaeology", "Arkeoloji"),
    Module("astronomy", "Astronomi"),
    Module("chemistry", "Kimyasal Analiz"),
    Module("spectral", "Spektral Analiz"),
    Module("thermal", "Termal Analiz"),
    Module("magnetometer", "Manyetometre"),
    Module("gravimeter", "Gravimetre"),
    Module("ert", "Elektrik Direnç"),
    Module("gpr", "GPR"),
    Module("seismic", "Sismik"),
    Module("hydro", "Hidrojeoloji"),
    Module("botany", "Botanik"),
    Module("soil", "Toprak"),
    Module("water", "Su"),
    Module("finance", "SyFinansOtağı"),
]


def enabled_modules():
    return [module for module in MODULES if module.enabled]
