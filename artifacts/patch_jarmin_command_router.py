from pathlib import Path


path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

old = """        self.intent_engine = intent_engine
        self.command_router = command_router
        self.device_bridge = device_bridge
"""

new = """        self.intent_engine = intent_engine

        if command_router is None:
            from .command_router import (
                CommandRouter,
            )

            command_router = CommandRouter()

        self.command_router = command_router
        self.device_bridge = device_bridge
"""

if old not in text:
    if (
        "if command_router is None:"
        not in text
    ):
        raise RuntimeError(
            "CommandRouter ekleme bölümü bulunamadı."
        )
else:
    text = text.replace(
        old,
        new,
        1,
    )

path.write_text(
    text,
    encoding="utf-8",
)

print("JARMIN_COMMAND_ROUTER_PATCH_OK")
