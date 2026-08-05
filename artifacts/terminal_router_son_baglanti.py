from __future__ import annotations

import ast
import re
from pathlib import Path


path = Path(
    "src/syk_simulasyon/runtime_ui_sunucusu.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

marker = "# SYK_TERMINAL_ROUTER_RUNTIME_BAGLANTISI"

if marker in text:
    text = text.split(
        marker,
        1,
    )[0].rstrip() + "\n"

text = re.sub(
    r"(?m)^[ \t]*from "
    r"syk_simulasyon\.syk_ui_runtime\.terminal_routes "
    r"import .*?\r?\n",
    "",
    text,
)

text = re.sub(
    r"(?m)^[ \t]*from __future__ import annotations[ \t]*\r?\n",
    "",
    text,
)

text = (
    "from __future__ import annotations\n\n"
    + text.lstrip()
)

ast.parse(
    text,
    filename=str(path),
)

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
    "TERMINAL_ROUTER_SON_BAGLANTI_OK"
)