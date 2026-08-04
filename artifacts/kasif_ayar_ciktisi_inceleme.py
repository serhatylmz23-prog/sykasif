from pathlib import Path
import ast


path = Path(
    "src/syk_jarmin/runtime/integration_runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

tree = ast.parse(text)

target = None

for node in ast.walk(tree):
    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ) and node.name in {
        "update_settings",
        "apply_settings",
        "snapshot",
    }:
        start = node.lineno
        end = node.end_lineno

        print()
        print(
            f"=== {node.name} "
            f"SATIR {start}-{end} ==="
        )

        lines = text.splitlines()

        for number in range(
            start,
            end + 1,
        ):
            print(
                f"{number:04d}: "
                f"{lines[number - 1]}"
            )

        if node.name == "update_settings":
            target = node

if target is None:
    raise RuntimeError(
        "update_settings metodu bulunamadı."
    )

print()
print("KASIF_AYAR_CIKTISI_INCELEME_OK")
