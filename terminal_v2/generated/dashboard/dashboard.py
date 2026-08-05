class Dashboard:
    NAME = "dashboard"

    def status(self) -> dict[str, str]:
        return {
            "module": self.NAME,
            "status": "READY",
        }
