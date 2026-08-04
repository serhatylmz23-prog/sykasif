from __future__ import annotations

import ast
from pathlib import Path


runtime_path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

integration_path = Path(
    "src/syk_jarmin/runtime/integration_runtime.py"
)

runtime_text = runtime_path.read_text(
    encoding="utf-8"
)

integration_text = integration_path.read_text(
    encoding="utf-8"
)

tree = ast.parse(integration_text)

expected: set[str] = set()

for node in ast.walk(tree):
    if not isinstance(node, ast.Attribute):
        continue

    owner = node.value

    if not isinstance(owner, ast.Attribute):
        continue

    if owner.attr != "runtime":
        continue

    if not isinstance(owner.value, ast.Name):
        continue

    if owner.value.id != "self":
        continue

    expected.add(node.attr)


# JarminRuntime sınıfında zaten bulunan metotlar.
existing_methods = {
    "start",
    "stop",
    "execute",
    "process",
    "handle",
    "run",
    "ask",
    "history",
    "clear_history",
    "snapshot",
}


aliases = {
    "assistant": "self",
    "core": "self",
    "runtime": "self",
    "kasif": "self",
    "jarmin": "self",
    "notifications": "self.notification_router",
    "notification": "self.notification_router",
    "commands": "self.command_router",
    "command": "self.command_router",
    "devices": "self.device_bridge",
    "device": "self.device_bridge",
    "voice": "self.voice_runtime",
    "memory": "self.conversation_memory",
    "intents": "self.intent_engine",
    "intent": "self.intent_engine",
}


unknown = sorted(
    name
    for name in expected
    if (
        name not in aliases
        and name not in existing_methods
    )
)

if unknown:
    raise RuntimeError(
        "Tanımlanmamış sözleşme beklentileri: "
        + ", ".join(unknown)
    )


begin_marker = (
    "        # BEGIN "
    "SYK_JARMIN_INTEGRATION_CONTRACT\n"
)

end_marker = (
    "        # END "
    "SYK_JARMIN_INTEGRATION_CONTRACT\n"
)


contract_lines = [
    begin_marker.rstrip("\n"),
    "        # Entegrasyon katmanı uyumluluk alanları.",
]

for name in sorted(expected):
    if name in aliases:
        contract_lines.append(
            f"        self.{name} = {aliases[name]}"
        )

contract_lines.append(
    end_marker.rstrip("\n")
)

contract = "\n".join(
    contract_lines
) + "\n"


# Önceki sözleşme bloklarını temizle.
markers = [
    (
        "        # BEGIN SYK_JARMIN_RUNTIME_CONTRACT\n",
        "        # END SYK_JARMIN_RUNTIME_CONTRACT\n",
    ),
    (
        begin_marker,
        end_marker,
    ),
]

for begin, end in markers:
    if begin in runtime_text and end in runtime_text:
        before, remainder = runtime_text.split(
            begin,
            1,
        )

        _, after = remainder.split(
            end,
            1,
        )

        runtime_text = before + after


anchor = (
    "        self.maximum_history = "
    "maximum_history\n"
)

if anchor not in runtime_text:
    raise RuntimeError(
        "JarminRuntime sözleşme ekleme "
        "noktası bulunamadı."
    )

runtime_text = runtime_text.replace(
    anchor,
    anchor + "\n" + contract,
    1,
)

runtime_path.write_text(
    runtime_text,
    encoding="utf-8",
)

print(
    "JARMIN_RUNTIME_CONTRACT_PATCH_OK"
)

print(
    "EXPECTED_ATTRIBUTES",
    ",".join(sorted(expected)),
)

print(
    "ALIASES_ADDED",
    ",".join(
        sorted(
            expected.intersection(
                aliases
            )
        )
    ),
)

print(
    "EXISTING_METHODS",
    ",".join(
        sorted(
            expected.intersection(
                existing_methods
            )
        )
    ),
)
