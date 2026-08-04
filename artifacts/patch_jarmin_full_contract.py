from pathlib import Path
import re


path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

begin = (
    "        # BEGIN "
    "SYK_JARMIN_INTEGRATION_CONTRACT\n"
)

end = (
    "        # END "
    "SYK_JARMIN_INTEGRATION_CONTRACT\n"
)

contract = """        # BEGIN SYK_JARMIN_INTEGRATION_CONTRACT
        # Entegrasyon katmanı için tam
        # geriye dönük uyumluluk sözleşmesi.
        self.assistant = self
        self.core = self
        self.runtime = self
        self.kasif = self
        self.jarmin = self

        self.notifications = self.notification_router
        self.notification = self.notification_router

        self.voice = self.voice_runtime

        self.commands = self.command_router
        self.command = self.command_router

        self.devices = self.device_bridge
        self.device = self.device_bridge

        self.memory = self.conversation_memory

        self.intent = self.intent_engine
        self.intents = self.intent_engine

        self.name = self.assistant_name
        self.display_name = self.assistant_name
        self.status = self._state
        # END SYK_JARMIN_INTEGRATION_CONTRACT
"""

# Daha önce eklenen iki farklı sözleşme
# bloğunu güvenli şekilde kaldır.
patterns = (
    (
        r"        # BEGIN "
        r"SYK_JARMIN_RUNTIME_CONTRACT\n"
        r".*?"
        r"        # END "
        r"SYK_JARMIN_RUNTIME_CONTRACT\n"
    ),
    (
        r"        # BEGIN "
        r"SYK_JARMIN_INTEGRATION_CONTRACT\n"
        r".*?"
        r"        # END "
        r"SYK_JARMIN_INTEGRATION_CONTRACT\n"
    ),
)

for pattern in patterns:
    text = re.sub(
        pattern,
        "",
        text,
        flags=re.DOTALL,
    )

anchor = (
    "        self.maximum_history = "
    "maximum_history\n"
)

if anchor not in text:
    raise RuntimeError(
        "JarminRuntime sözleşme ekleme "
        "noktası bulunamadı."
    )

text = text.replace(
    anchor,
    anchor + "\n" + contract,
    1,
)

path.write_text(
    text,
    encoding="utf-8",
)

print("JARMIN_FULL_CONTRACT_PATCH_OK")
print("RUNTIME_PATH", path)
