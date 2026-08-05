from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

finans_path = Path(
    "src/syk_simulasyon/syk_ui_runtime/"
    "syfinans_runtime_routes.py"
)

finans_var = finans_path.is_file()


def satir_araliklarini_sil(
    source: str,
    ranges: list[tuple[int, int]],
) -> str:
    lines = source.splitlines(
        keepends=True
    )

    for start, end in sorted(
        ranges,
        reverse=True,
    ):
        del lines[start - 1:end]

    return "".join(lines)


tree = ast.parse(
    text,
    filename=str(path),
)

silinecekler: list[tuple[int, int]] = []

for node in ast.walk(tree):
    if isinstance(
        node,
        ast.ImportFrom,
    ):
        module = node.module or ""

        if module in {
            "syk_ui_runtime.terminal_routes",
            "syk_ui_runtime.syfinans_runtime_routes",
        }:
            silinecekler.append(
                (
                    node.lineno,
                    node.end_lineno or node.lineno,
                )
            )

    if isinstance(
        node,
        ast.If,
    ):
        cagri_adlari: set[str] = set()

        for alt in ast.walk(node):
            if not (
                isinstance(alt, ast.Call)
                and isinstance(
                    alt.func,
                    ast.Attribute,
                )
                and alt.func.attr
                == "include_router"
            ):
                continue

            for arg in alt.args:
                if isinstance(
                    arg,
                    ast.Name,
                ):
                    cagri_adlari.add(
                        arg.id
                    )

        if cagri_adlari.intersection(
            {
                "terminal_router",
                "syk_terminal_router",
                "finans_router",
                "syk_finans_router",
            }
        ):
            silinecekler.append(
                (
                    node.lineno,
                    node.end_lineno or node.lineno,
                )
            )

text = satir_araliklarini_sil(
    text,
    silinecekler,
)

temiz_satirlar = []

for line in text.splitlines(
    keepends=True
):
    if (
        "SYK_TERMINAL_ROUTER_"
        in line
        or "SYK_FINANS_ROUTER_"
        in line
    ):
        continue

    temiz_satirlar.append(
        line
    )

text = "".join(
    temiz_satirlar
)

tree = ast.parse(
    text,
    filename=str(path),
)

import_block = (
    "from .syk_ui_runtime.terminal_routes import (\n"
    "    terminal_router as syk_terminal_router,\n"
    ")\n"
)

if finans_var:
    import_block += (
        "from .syk_ui_runtime.syfinans_runtime_routes import (\n"
        "    finans_router as syk_finans_router,\n"
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

text = "".join(
    lines
)

tree = ast.parse(
    text,
    filename=str(path),
)

factory = next(
    (
        node
        for node in tree.body
        if isinstance(
            node,
            ast.FunctionDef,
        )
        and node.name
        == "uygulama_olustur"
    ),
    None,
)

if factory is None:
    raise RuntimeError(
        "uygulama_olustur() bulunamadi."
    )

return_node = next(
    (
        node
        for node in factory.body
        if isinstance(
            node,
            ast.Return,
        )
        and isinstance(
            node.value,
            ast.Name,
        )
        and node.value.id
        == "uygulama"
    ),
    None,
)

if return_node is None:
    raise RuntimeError(
        "uygulama_olustur() icinde "
        "return uygulama bulunamadi."
    )

block = (
    "    # SYK_TERMINAL_ROUTER_GERCEK_FABRIKA\n"
    "    if not any(\n"
    "        getattr(route, \"path\", None)\n"
    "        == \"/api/syk-ui/terminal/state\"\n"
    "        for route in uygulama.routes\n"
    "    ):\n"
    "        uygulama.include_router(\n"
    "            syk_terminal_router\n"
    "        )\n\n"
)

if finans_var:
    block += (
        "    # SYK_FINANS_ROUTER_GERCEK_FABRIKA\n"
        "    if not any(\n"
        "        getattr(route, \"path\", None)\n"
        "        == \"/syfinans/runtime\"\n"
        "        for route in uygulama.routes\n"
        "    ):\n"
        "        uygulama.include_router(\n"
        "            syk_finans_router\n"
        "        )\n\n"
    )

lines = text.splitlines(
    keepends=True
)

lines.insert(
    return_node.lineno - 1,
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
    "TERMINAL_FINANS_GERCEK_FABRIKA_BIRLESTIRME_OK"
)
print(
    "FINANS_ROUTER",
    "VAR" if finans_var else "YOK",
)