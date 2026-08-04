from __future__ import annotations

import ast
from pathlib import Path

path = Path(r"tests\test_pyproject_dagitim_sozlesmesi.py")

required_packages = {
    "syk_core/ecosystem",
    "syk_core/integration",
    "syk_core/learning",
    "syk_core/live_analysis",
    "syk_core/live_persistence",
    "syk_core/ovm",
}

text = path.read_text(encoding="utf-8-sig")
tree = ast.parse(text, filename=str(path))

candidates: list[tuple[int, int, list[str]]] = []

for node in ast.walk(tree):
    if not isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        continue

    values: list[str] = []

    for element in node.elts:
        if isinstance(element, ast.Constant) and isinstance(element.value, str):
            values.append(element.value)

    package_values = [
        value
        for value in values
        if "/" in value
        or value.startswith("syk_")
        or value.startswith("syk_core")
    ]

    if len(package_values) >= 3:
        candidates.append(
            (
                node.lineno,
                node.end_lineno or node.lineno,
                values,
            )
        )

if not candidates:
    raise RuntimeError(
        "Paket sözleşmesini içeren liste, küme veya demet bulunamadı."
    )

start_line, end_line, existing_values = max(
    candidates,
    key=lambda item: len(item[2]),
)

missing = sorted(required_packages.difference(existing_values))

if not missing:
    print("EKSİK_PAKET_YOK")
    raise SystemExit(0)

lines = text.splitlines()

opening_line = lines[start_line - 1]
indent = opening_line[: len(opening_line) - len(opening_line.lstrip())]
item_indent = indent + "    "

for line_number in range(start_line, end_line + 1):
    stripped = lines[line_number - 1].lstrip()

    if stripped.startswith(("'", '"')):
        current_indent = lines[line_number - 1][
            : len(lines[line_number - 1])
            - len(stripped)
        ]

        if current_indent:
            item_indent = current_indent
            break

closing_index = end_line - 1

new_lines = [
    f'{item_indent}"{package}",'
    for package in missing
]

lines[closing_index:closing_index] = new_lines

path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print("EKLENEN_PAKETLER")
for package in missing:
    print(f"+ {package}")
