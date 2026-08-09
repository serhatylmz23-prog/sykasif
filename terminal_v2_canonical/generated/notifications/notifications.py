class Notifications:
    NAME = "notifications"

    def status(self) -> dict[str, str]:
        return {
            "module": self.NAME,
            "status": "READY",
        }
