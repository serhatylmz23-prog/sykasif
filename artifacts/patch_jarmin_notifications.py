from pathlib import Path

path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

old = """        self.voice_runtime = voice_runtime
        self.notification_router = notification_router
        self.conversation_memory = conversation_memory
"""

new = """        self.voice_runtime = voice_runtime

        if notification_router is None:
            from .notification_router import (
                NotificationRouter,
            )

            notification_router = (
                NotificationRouter()
            )

        self.notification_router = (
            notification_router
        )

        # Eski entegrasyon katmanının beklediği
        # geriye dönük uyumluluk adı.
        self.notifications = (
            notification_router
        )

        self.conversation_memory = (
            conversation_memory
        )
"""

if old not in text:
    if (
        "self.notifications"
        not in text
    ):
        raise RuntimeError(
            "JarminRuntime kurucu bölümü "
            "otomatik olarak bulunamadı."
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

print(
    "JARMIN_NOTIFICATIONS_PATCH_OK"
)
