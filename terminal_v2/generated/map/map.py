class Map:
    NAME = "map"

    def status(self) -> dict[str, str]:
        return {
            "module": self.NAME,
            "status": "READY",
        }
