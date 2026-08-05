from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

eski_blok = '''    # SYK_TERMINAL_ROUTER_GERCEK_FABRIKA
    if not any(
        getattr(route, "path", None)
        == "/api/syk-ui/terminal/state"
        for route in uygulama.routes
    ):
        uygulama.router.include_router(
            syk_terminal_router
        )

    # SYK_FINANS_ROUTER_GERCEK_FABRIKA
    if not any(
        getattr(route, "path", None)
        == "/syfinans/runtime"
        for route in uygulama.routes
    ):
        uygulama.router.include_router(
            syk_finans_router
        )
'''

yeni_blok = '''    # SYK_TERMINAL_FINANS_DOGRUDAN_ROUTE_BAGLANTISI
    mevcut_yollar = {
        getattr(route, "path", None)
        for route in uygulama.router.routes
    }

    for route in syk_terminal_router.routes:
        if getattr(route, "path", None) not in mevcut_yollar:
            uygulama.router.routes.append(route)
            mevcut_yollar.add(
                getattr(route, "path", None)
            )

    for route in syk_finans_router.routes:
        if getattr(route, "path", None) not in mevcut_yollar:
            uygulama.router.routes.append(route)
            mevcut_yollar.add(
                getattr(route, "path", None)
            )
'''

if eski_blok not in text:
    raise RuntimeError(
        "Eski terminal/finans bağlantı bloğu bulunamadı."
    )

text = text.replace(
    eski_blok,
    yeni_blok,
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
    "TERMINAL_FINANS_DOGRUDAN_ROUTE_BAGLANTISI_OK"
)