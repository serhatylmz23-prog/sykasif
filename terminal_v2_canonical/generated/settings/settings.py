class Settings:
    NAME = "settings"

    def status(self) -> dict[str, str]:
        return {
            "module": self.NAME,
            "status": "READY",
        }
