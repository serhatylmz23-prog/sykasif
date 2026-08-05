from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_simulasyon/runtime_ui_sunucusu.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

marker = "SYK_TERMINAL_ROUTER_RUNTIME_BAGLANTISI"

block = """
# SYK_TERMINAL_ROUTER_RUNTIME_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.terminal_routes import (
    terminal_router as syk_terminal_router,
)

if not any(
    getattr(route, "path", None)
    == "/api/syk-ui/terminal/state"
    for route in app.routes
):
    app.include_router(
        syk_terminal_router
    )
"""

ast.parse(
    text,
    filename=str(path),
)

if marker not in text:
    text = (
        text.rstrip()
        + "\n\n"
        + block.strip()
        + "\n"
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
    "TERMINAL_ROUTER_GUVENLI_BAGLANDI"
)