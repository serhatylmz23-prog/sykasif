from __future__ import annotations

import ast
from pathlib import Path

path = Path("tests/test_pyproject_dagitim_sozlesmesi.py")
text = path.read_text(encoding="utf-8-sig")
tree = ast.parse(text, filename=str(path))

target_function = "test_src_altinda_tek_urun_paketi_var"

expected_packages = [
    "syk_core",
    "syk_core/ecosystem",
    "syk_core/entegrasyon",
    "syk_core/integration",
    "syk_core/learning",
    "syk_core/live_analysis",
    "syk_core/live_persistence",
    "syk_core/ovm",
    "syk_finans_otagi",
    "syk_jarmin",
    "syk_simulasyon",
]

target_node: ast.FunctionDef | ast.AsyncFunctionDef | None = None

for node in tree.body:
    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == target_function
    ):
        target_node = node
        break

if target_node is None:
    raise RuntimeError(
        f"Hedef test fonksiyonu bulunamadı: {target_function}"
    )

assert_node: ast.Assert | None = None

for node in ast.walk(target_node):
    if not isinstance(node, ast.Assert):
        continue

    comparison = node.test

    if not isinstance(comparison, ast.Compare):
        continue

    if not isinstance(comparison.left, ast.Name):
        continue

    if comparison.left.id != "paketler":
        continue

    assert_node = node
    break

if assert_node is None:
    raise RuntimeError(
        "Hedef 'assert paketler == [...]' sözleşmesi bulunamadı."
    )

if assert_node.end_lineno is None:
    raise RuntimeError(
        "Assert bitiş satırı Python AST tarafından belirlenemedi."
    )

lines = text.splitlines()

start_index = assert_node.lineno - 1
end_index = assert_node.end_lineno

original_line = lines[start_index]
indent = original_line[: len(original_line) - len(original_line.lstrip())]

replacement = [
    f"{indent}assert paketler == [",
    *[
        f'{indent}    "{package}",'
        for package in expected_packages
    ],
    f"{indent}]",
]

lines[start_index:end_index] = replacement

path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print("DAGITIM_SOZLESMESI_LISTESI_GUNCELLENDI")

for package in expected_packages:
    print(f"+ {package}")
