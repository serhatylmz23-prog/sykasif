from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

tree = ast.parse(
    text,
    filename=str(path),
)

import_marker = (
    "from .syk_ui_runtime.terminal_routes import"
)

if import_marker not in text:
    import_block = (
        "from .syk_ui_runtime.terminal_routes import (\n"
        "    terminal_router as syk_terminal_router,\n"
        ")\n"
    )

    insertion_line = 0

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            insertion_line = max(
                insertion_line,
                node.end_lineno or node.lineno,
            )

    lines = text.splitlines(
        keepends=True
    )

    lines.insert(
        insertion_line,
        import_block,
    )

    text = "".join(lines)

tree = ast.parse(
    text,
    filename=str(path),
)

factory = None

for node in tree.body:
    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "uygulama_olustur"
    ):
        factory = node
        break

if factory is None:
    raise RuntimeError(
        "uygulama_olustur() bulunamadi."
    )

return_node = None

for node in factory.body:
    if (
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Name)
        and node.value.id == "uygulama"
    ):
        return_node = node
        break

if return_node is None:
    raise RuntimeError(
        "uygulama_olustur() icinde "
        "'return uygulama' bulunamadi."
    )

marker = (
    "SYK_TERMINAL_ROUTER_GERCEK_FABRIKA_BAGLANTISI"
)

if marker not in text:
    block = (
        "    # SYK_TERMINAL_ROUTER_GERCEK_FABRIKA_BAGLANTISI\n"
        "    if not any(\n"
        "        getattr(route, \"path\", None)\n"
        "        == \"/api/syk-ui/terminal/state\"\n"
        "        for route in uygulama.routes\n"
        "    ):\n"
        "        uygulama.include_router(\n"
        "            syk_terminal_router\n"
        "        )\n\n"
    )

    lines = text.splitlines(
        keepends=True
    )

    lines.insert(
        return_node.lineno - 1,
        block,
    )

    text = "".join(lines)

ast.parse(
    text,
    filename=str(path),
)

path.write_text(
    text,
    encoding="utf-8",
    newline="\n",
)

print(
    "TERMINAL_ROUTER_GERCEK_FABRIKAYA_BAGLANDI"
)