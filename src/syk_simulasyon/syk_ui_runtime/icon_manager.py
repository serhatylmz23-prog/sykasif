"""
SPR-003-UI-0008
SyKaşif Icon Manager
"""

from dataclasses import dataclass
from pathlib import Path


ICON_ROOT = Path(__file__).resolve().parent / "static" / "icons"


@dataclass(frozen=True)
class Icon:

    id: str
    filename: str


ICONS = {

    "logo": Icon("logo", "logo.svg"),
    "syframe": Icon("syframe", "syframe.svg"),
    "map": Icon("map", "map.svg"),
    "gps": Icon("gps", "gps.svg"),
    "sonar": Icon("sonar", "sonar.svg"),
    "lidar": Icon("lidar", "lidar.svg"),
    "geology": Icon("geology", "geology.svg"),
    "history": Icon("history", "history.svg"),
    "analysis": Icon("analysis", "analysis.svg"),
    "report": Icon("report", "report.svg"),
    "finance": Icon("finance", "finance.svg"),

}


class IconManager:

    def available(self):

        return list(ICONS.values())

    def get(self, icon_id: str):

        if icon_id not in ICONS:
            raise KeyError(icon_id)

        return ICON_ROOT / ICONS[icon_id].filename
