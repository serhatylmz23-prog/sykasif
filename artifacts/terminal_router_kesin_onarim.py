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

terminal_import_pattern = re.compile(
    r"from\s+syk_simulasyon\.syk_ui_runtime\.terminal_routes"
    r"\s+import\s+terminal_router"
)

future_pattern = re.compile(
    r"from\s+__future__\s+import\s+annotations"
)

text = terminal_import_pattern.sub(
    "",
    text,
)

text = future_pattern.sub(
    "",
    text,
)

text = re.sub(
    r"(?m)^[ \t]*# SYK_TERMINAL_ROUTER_RUNTIME_BAGLANTISI[ \t]*\r?\n?",
    "",
    text,
)

text = re.sub(
    r"""
    (?ms)
    if\s+not\s+any\(
        .*?
        /api/syk-ui/terminal/state
        .*?
    \):\s*
        app\.include_router\(
            \s*terminal_router\s*
        \)
    """,
    "",
    text,
    flags=re.VERBOSE,
)

text = text.lstrip()

header = (
    "from __future__ import annotations\n\n"
    "from syk_simulasyon.syk_ui_runtime.terminal_routes "
    "import terminal_router\n\n"
)

text = header + text

ast.parse(
    text,
    filename=str(path),
)

route_block = (
    "\n\n"
    "# SYK_TERMINAL_ROUTER_RUNTIME_BAGLANTISI\n"
    "if not any(\n"
    "    getattr(route, \"path\", None)\n"
    "    == \"/api/syk-ui/terminal/state\"\n"
    "    for route in app.routes\n"
    "):\n"
    "    app.include_router(\n"
    "        terminal_router\n"
    "    )\n"
)

if (
    "/api/syk-ui/terminal/state"
    not in text
):
    text = (
        text.rstrip()
        + route_block
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
    "TERMINAL_ROUTER_KESIN_ONARIM_OK"
)