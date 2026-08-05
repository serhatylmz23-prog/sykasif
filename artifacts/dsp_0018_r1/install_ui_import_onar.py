from __future__ import annotations

import ast
import re
from pathlib import Path


src_root = Path("src")
test_path = Path("tests/test_map_workspace_ui.py")

if not test_path.is_file():
    raise RuntimeError(
        "Harita UI test dosyası bulunamadı."
    )

adaylar: list[Path] = []

for path in src_root.rglob("*.py"):
    try:
        text = path.read_text(
            encoding="utf-8-sig"
        )
    except UnicodeDecodeError:
        continue

    try:
        tree = ast.parse(
            text,
            filename=str(path),
        )
    except SyntaxError:
        continue

    if any(
        isinstance(node, ast.FunctionDef)
        and node.name == "install_ui"
        for node in ast.walk(tree)
    ):
        adaylar.append(path)

if not adaylar:
    raise RuntimeError(
        "install_ui() tanımı kaynaklarda bulunamadı."
    )

tercih_sirasi = (
    "syk_ui.py",
    "runtime_ui_sunucusu.py",
    "__init__.py",
)

adaylar.sort(
    key=lambda path: (
        tercih_sirasi.index(path.name)
        if path.name in tercih_sirasi
        else len(tercih_sirasi),
        len(path.parts),
        str(path),
    )
)

kaynak = adaylar[0]

relative = kaynak.relative_to(src_root)

module_parts = list(relative.with_suffix("").parts)

if module_parts[-1] == "__init__":
    module_parts.pop()

module_name = ".".join(module_parts)

test_text = test_path.read_text(
    encoding="utf-8-sig"
)

test_text = re.sub(
    (
        r"from\s+"
        r"syk_simulasyon\.syk_ui_runtime\.install\s+"
        r"import\s+install_ui"
    ),
    f"from {module_name} import install_ui",
    test_text,
)

ast.parse(
    test_text,
    filename=str(test_path),
)

test_path.write_text(
    test_text,
    encoding="utf-8",
    newline="\n",
)

print(
    "INSTALL_UI_KAYNAGI",
    kaynak,
)

print(
    "INSTALL_UI_MODULU",
    module_name,
)

print(
    "HARITA_UI_TEST_IMPORT_ONARIM_OK"
)