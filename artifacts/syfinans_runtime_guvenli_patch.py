from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/api_routes.py"
)

text = path.read_text(
    encoding="utf-8"
)

import_text = (
    "from .syfinans_runtime_routes import (\n"
    "    finans_router,\n"
    ")\n"
)

include_text = (
    "\n"
    "router.include_router(\n"
    "    finans_router\n"
    ")\n"
)


def parse(source: str) -> ast.Module:
    return ast.parse(
        source,
        filename=str(path),
    )


tree = parse(text)

if (
    "from .syfinans_runtime_routes import"
    not in text
):
    body = list(tree.body)

    insertion_line = 0

    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(
            body[0].value,
            ast.Constant,
        )
        and isinstance(
            body[0].value.value,
            str,
        )
    ):
        insertion_line = (
            body[0].end_lineno
            or body[0].lineno
        )

    for node in body:
        if isinstance(
            node,
            (ast.Import, ast.ImportFrom),
        ):
            insertion_line = max(
                insertion_line,
                node.end_lineno
                or node.lineno,
            )
            continue

        if insertion_line > 0:
            break

    lines = text.splitlines(
        keepends=True
    )

    lines.insert(
        insertion_line,
        import_text,
    )

    text = "".join(lines)

tree = parse(text)

router_var = any(
    isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name)
        and target.id == "router"
        for target in node.targets
    )
    for node in tree.body
)

if not router_var:
    raise RuntimeError(
        "Modül seviyesinde router "
        "nesnesi bulunamadı."
    )

include_signature = (
    "router.include_router(\n"
    "    finans_router\n"
    ")"
)

if include_signature not in text:
    text = (
        text.rstrip()
        + "\n"
        + include_text
    )

parse(text)

import_sayisi = text.count(
    "from .syfinans_runtime_routes import"
)

router_kayit_sayisi = text.count(
    include_signature
)

if import_sayisi != 1:
    raise RuntimeError(
        "SyFinans import sayısı hatalı: "
        f"{import_sayisi}"
    )

if router_kayit_sayisi != 1:
    raise RuntimeError(
        "SyFinans router kayıt sayısı hatalı: "
        f"{router_kayit_sayisi}"
    )

path.write_text(
    text,
    encoding="utf-8",
)

parse(
    path.read_text(
        encoding="utf-8"
    )
)

print("SYFINANS_RUNTIME_GUVENLI_PATCH_OK")
print("IMPORT_SAYISI", import_sayisi)
print(
    "ROUTER_KAYIT_SAYISI",
    router_kayit_sayisi,
)