from dataclasses import asdict

from .audio_manager import AudioManager
from .brand_title_manager import BrandTitleManager
from .environment import EnvironmentManager
from .image_manager import ImageManager
from .runtime_manager import RuntimeManager
from .syframe_manager import SyFrameManager
from .theme_manager import ThemeManager


class UIRuntimeState:
    def __init__(self):
        self.runtime = RuntimeManager()
        self.theme = ThemeManager()
        self.environment = EnvironmentManager()
        self.audio = AudioManager()
        self.images = ImageManager()
        self.brand = BrandTitleManager()
        self.syframe = SyFrameManager()

    def snapshot(self) -> dict:
        return {
            "active_module": asdict(self.runtime.active),
            "theme": asdict(self.theme.current),
            "environment": asdict(self.environment.current),
            "audio": asdict(self.audio.current),
            "brand": {
                "title": asdict(self.brand.current),
                "visible": self.brand.visible,
            },
            "syframe": {
                "state": asdict(self.syframe.state),
                "mode": self.syframe.mode,
                "visible": self.syframe.visible,
                "confidence": self.syframe.confidence,
            },
            "assets": {
                "audio_ready": self.audio.is_ready(),
                "images_ready": self.images.is_ready(),
            },
        }
