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

marker = "# SYK_RESEARCH_RUNTIME_ROUTER_BAGLANTISI"

if marker in text:
    text = text.split(
        marker,
        1,
    )[0].rstrip() + "\n"

block = r'''
# SYK_RESEARCH_RUNTIME_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.research_routes import (
    research_router as syk_research_router,
)

_syk_research_paths = {
    getattr(route, "path", None)
    for route in syk_research_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_research_paths
]

_syk_research_insert_index = len(
    app.router.routes
)

for _syk_index, _syk_route in enumerate(
    app.router.routes
):
    _syk_path = getattr(
        _syk_route,
        "path",
        "",
    )

    if (
        "{" in _syk_path
        and _syk_path.startswith("/api/syk-ui/")
    ):
        _syk_research_insert_index = _syk_index
        break

for _syk_research_route in reversed(
    syk_research_router.routes
):
    app.router.routes.insert(
        _syk_research_insert_index,
        _syk_research_route,
    )
'''

text = (
    text.rstrip()
    + "\n\n"
    + block.strip()
    + "\n"
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

path.write_text(
    text,
    encoding="utf-8",
    newline="\n",
)

print(
    "RESEARCH_RUNTIME_ROUTER_UI_SUNUCUSUNA_BAGLANDI"
)