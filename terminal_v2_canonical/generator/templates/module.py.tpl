class {{CLASS_NAME}}:
    NAME = "{{MODULE_NAME}}"

    def status(self) -> dict[str, str]:
        return {
            "module": self.NAME,
            "status": "READY",
        }
