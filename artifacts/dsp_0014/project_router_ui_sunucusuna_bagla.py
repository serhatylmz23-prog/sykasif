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

marker = "SYK_PROJECT_RUNTIME_ROUTER_BAGLANTISI"

if marker not in text:
    block = """
# SYK_PROJECT_RUNTIME_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.project_routes import (
    project_router as syk_project_router,
)

_syk_project_paths = {
    getattr(route, "path", None)
    for route in app.router.routes
}

for _syk_project_route in syk_project_router.routes:
    if (
        getattr(_syk_project_route, "path", None)
        not in _syk_project_paths
    ):
        app.router.routes.append(
            _syk_project_route
        )
        _syk_project_paths.add(
            getattr(_syk_project_route, "path", None)
        )
"""

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
    "PROJECT_RUNTIME_ROUTER_UI_SUNUCUSUNA_BAGLANDI"
)