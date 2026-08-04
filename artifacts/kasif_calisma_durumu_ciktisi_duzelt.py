from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

tree = ast.parse(text)
lines = text.splitlines()


target_class = None
target_method = None

for node in tree.body:
    if (
        isinstance(node, ast.ClassDef)
        and node.name == "JarminRuntime"
    ):
        target_class = node
        break

if target_class is None:
    raise RuntimeError(
        "JarminRuntime sınıfı bulunamadı."
    )

for node in target_class.body:
    if (
        isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and node.name == "snapshot"
    ):
        target_method = node
        break

if target_method is None:
    raise RuntimeError(
        "JarminRuntime.snapshot metodu bulunamadı."
    )


marker = (
    "        # BEGIN "
    "SYK_KASIF_DURUM_CIKTISI"
)

if marker not in text:
    return_node = next(
        (
            node
            for node in target_method.body
            if isinstance(node, ast.Return)
        ),
        None,
    )

    if return_node is None:
        raise RuntimeError(
            "snapshot dönüş noktası bulunamadı."
        )

    insertion_index = (
        return_node.lineno - 1
    )

    block = '''
        # BEGIN SYK_KASIF_DURUM_CIKTISI
        assistant_settings = dict(
            getattr(
                self,
                "_settings",
                {},
            )
        )

        voice_snapshot = None

        voice_snapshot_method = getattr(
            self.voice_runtime,
            "snapshot",
            None,
        )

        if callable(
            voice_snapshot_method
        ):
            voice_snapshot = (
                voice_snapshot_method()
            )

        notification_snapshot = None

        notification_snapshot_method = getattr(
            self.notification_router,
            "snapshot",
            None,
        )

        if callable(
            notification_snapshot_method
        ):
            notification_snapshot = (
                notification_snapshot_method()
            )

        unsigned["assistant"] = {
            "name": self.assistant_name,
            "display_name": (
                self.assistant_name
            ),
            "active": bool(
                assistant_settings.get(
                    "active",
                    True,
                )
            ),
            "voice_enabled": bool(
                assistant_settings.get(
                    "voice_enabled",
                    True,
                )
            ),
            "notification_enabled": bool(
                assistant_settings.get(
                    "notification_enabled",
                    True,
                )
            ),
            "wake_words": [
                "Kaşif",
                "Babuş",
            ],
            "status": self._state,
        }

        unsigned["voice"] = (
            voice_snapshot
        )

        unsigned["notifications"] = (
            notification_snapshot
        )
        # END SYK_KASIF_DURUM_CIKTISI
'''.strip("\n").splitlines()

    lines[
        insertion_index:insertion_index
    ] = block

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


updated = path.read_text(
    encoding="utf-8"
)

ast.parse(updated)

print(
    "KASIF_DURUM_CIKTISI_DUZELTILDI"
)
