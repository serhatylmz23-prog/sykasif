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

import_text = (
    "from .syk_ui_runtime.terminal_routes import (\n"
    "    terminal_router as syk_terminal_router,\n"
    ")\n"
)

import_exists = any(
    isinstance(node, ast.ImportFrom)
    and node.module == "syk_ui_runtime.terminal_routes"
    and any(
        alias.name == "terminal_router"
        for alias in node.names
    )
    for node in tree.body
)

if not import_exists:
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
        import_text,
    )

    text = "".join(
        lines
    )

tree = ast.parse(
    text,
    filename=str(path),
)

target_return_line = None

for node in tree.body:
    if not (
        isinstance(node, ast.ClassDef)
        and node.name == "RuntimeFastApiSunucusu"
    ):
        continue

    for item in node.body:
        if not (
            isinstance(
                item,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and item.name == "olustur"
        ):
            continue

        for statement in item.body:
            if (
                isinstance(statement, ast.Return)
                and isinstance(statement.value, ast.Name)
                and statement.value.id == "uygulama"
            ):
                target_return_line = statement.lineno
                break

if target_return_line is None:
    raise RuntimeError(
        "olustur() icindeki 'return uygulama' bulunamadi."
    )

marker = "SYK_TERMINAL_ROUTER_FASTAPI_FABRIKA_BAGLANTISI"

if marker not in text:
    block = (
        "        # SYK_TERMINAL_ROUTER_FASTAPI_FABRIKA_BAGLANTISI\n"
        "        if not any(\n"
        "            getattr(route, \"path\", None)\n"
        "            == \"/api/syk-ui/terminal/state\"\n"
        "            for route in uygulama.routes\n"
        "        ):\n"
        "            uygulama.include_router(\n"
        "                syk_terminal_router\n"
        "            )\n\n"
    )

    lines = text.splitlines(
        keepends=True
    )

    lines.insert(
        target_return_line - 1,
        block,
    )

    text = "".join(
        lines
    )

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
    "TERMINAL_ROUTER_FASTAPI_FABRIKASINA_BAGLANDI"
)