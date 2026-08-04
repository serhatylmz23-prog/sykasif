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

import_block = '''from .syfinans_runtime_routes import (
    finans_router,
)
'''

include_line = '''
router.include_router(
    finans_router
)
'''

if "finans_router" not in text:
    lines = text.splitlines(
        keepends=True
    )

    son_import = -1

    for index, line in enumerate(
        lines
    ):
        stripped = line.lstrip()

        if (
            stripped.startswith(
                "import "
            )
            or stripped.startswith(
                "from "
            )
        ):
            son_import = index

    if son_import < 0:
        raise RuntimeError(
            "api_routes.py içinde import bölümü bulunamadı."
        )

    lines.insert(
        son_import + 1,
        import_block,
    )

    text = "".join(
        lines
    )

if "router.include_router" not in text or (
    "router.include_router(\n"
    "    finans_router\n"
    ")"
    not in text
):
    text = (
        text.rstrip()
        + "\n"
        + include_line
        + "\n"
    )

path.write_text(
    text,
    encoding="utf-8",
)

ast.parse(
    path.read_text(
        encoding="utf-8"
    ),
    filename=str(
        path
    ),
)

print(
    "SYFINANS_RUNTIME_ROUTER_KAYDI_OK"
)