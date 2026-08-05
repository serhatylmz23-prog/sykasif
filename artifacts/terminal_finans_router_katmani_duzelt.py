from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

eski_terminal = (
    "        uygulama.include_router(\n"
    "            syk_terminal_router\n"
    "        )"
)

yeni_terminal = (
    "        uygulama.router.include_router(\n"
    "            syk_terminal_router\n"
    "        )"
)

eski_finans = (
    "        uygulama.include_router(\n"
    "            syk_finans_router\n"
    "        )"
)

yeni_finans = (
    "        uygulama.router.include_router(\n"
    "            syk_finans_router\n"
    "        )"
)

if eski_terminal not in text:
    raise RuntimeError(
        "Terminal router bağlantı bloğu bulunamadı."
    )

if eski_finans not in text:
    raise RuntimeError(
        "SyFinans router bağlantı bloğu bulunamadı."
    )

text = text.replace(
    eski_terminal,
    yeni_terminal,
    1,
)

text = text.replace(
    eski_finans,
    yeni_finans,
    1,
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
    "TERMINAL_FINANS_ROUTER_KATMANI_DUZELTILDI"
)