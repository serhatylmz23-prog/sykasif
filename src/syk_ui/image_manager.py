from dataclasses import dataclass
from pathlib import Path


IMAGE_ROOT = Path(__file__).resolve().parent / "static" / "images"


@dataclass(frozen=True)
class ImageAsset:
    id: str
    filename: str
    category: str
    required: bool = False


ASSETS = {
    "logo": ImageAsset("logo", "logo.png", "brand"),
    "syframe": ImageAsset("syframe", "syframe.png", "ui"),
    "module_hub": ImageAsset("module_hub", "module-hub.png", "ui"),
    "maps": ImageAsset("maps", "maps.png", "module"),
    "geology": ImageAsset("geology", "geology.png", "module"),
    "sonar": ImageAsset("sonar", "sonar.png", "module"),
    "frequency": ImageAsset("frequency", "frequency.png", "module"),
    "measurement": ImageAsset("measurement", "measurement.png", "module"),
    "lidar": ImageAsset("lidar", "lidar.png", "module"),
    "history": ImageAsset("history", "history.png", "module"),
    "finance": ImageAsset("finance", "finance.png", "module"),
}


class ImageManager:
    def available(self) -> list[ImageAsset]:
        return list(ASSETS.values())

    def get(self, asset_id: str) -> Path:
        if asset_id not in ASSETS:
            raise KeyError(f"Unknown image asset: {asset_id}")

        return IMAGE_ROOT / ASSETS[asset_id].filename

    def missing_files(self) -> list[Path]:
        return [
            IMAGE_ROOT / asset.filename
            for asset in ASSETS.values()
            if asset.required
            and not (IMAGE_ROOT / asset.filename).is_file()
        ]

    def is_ready(self) -> bool:
        return not self.missing_files()
