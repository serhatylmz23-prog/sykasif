from __future__ import annotations

import ast
from pathlib import Path

path = Path(
    "tests/test_pyproject_dagitim_sozlesmesi.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

package = "syk_core/runtime_terminal"

if package in text:
    print("RUNTIME_TERMINAL_ZATEN_KAYITLI")
    raise SystemExit(0)

tree = ast.parse(
    text,
    filename=str(path),
)

target = None

for node in ast.walk(tree):
    if not isinstance(node, ast.List):
        continue

    values = [
        element.value
        for element in node.elts
        if isinstance(
            element,
            ast.Constant,
        )
        and isinstance(
            element.value,
            str,
        )
    ]

    if (
        "syk_core/runtime_kernel" in values
        and "syk_finans_otagi" in values
    ):
        target = node
        break

if target is None:
    raise RuntimeError(
        "Dağıtım paket listesi bulunamadı."
    )

lines = text.splitlines()
insert_index = None
indent = "        "

for line_number in range(
    target.lineno,
    (target.end_lineno or target.lineno) + 1,
):
    line = lines[line_number - 1]

    if (
        "syk_finans_otagi"
        in line
    ):
        insert_index = line_number - 1
        indent = line[
            : len(line)
            - len(line.lstrip())
        ]
        break

if insert_index is None:
    raise RuntimeError(
        "Paket yerleştirme noktası bulunamadı."
    )

lines.insert(
    insert_index,
    f'{indent}"{package}",',
)

updated = "\n".join(lines) + "\n"

ast.parse(
    updated,
    filename=str(path),
)

path.write_text(
    updated,
    encoding="utf-8",
)

print(
    "RUNTIME_TERMINAL_DAGITIM_SOZLESMESINE_EKLENDI"
)
