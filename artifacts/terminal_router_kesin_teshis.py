from __future__ import annotations

import ast
import inspect
from pathlib import Path

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)
from syk_simulasyon.syk_ui_runtime import terminal_routes


ana_dosya = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

router_dosyasi = Path(
    "src/syk_simulasyon/syk_ui_runtime/terminal_routes.py"
)

ana_metin = ana_dosya.read_text(
    encoding="utf-8-sig"
)

router_metin = router_dosyasi.read_text(
    encoding="utf-8-sig"
)

ana_agac = ast.parse(
    ana_metin,
    filename=str(ana_dosya),
)

router_agac = ast.parse(
    router_metin,
    filename=str(router_dosyasi),
)

print("=== TERMINAL ROUTER NESNELERI ===")

for ad, deger in vars(
    terminal_routes
).items():
    if hasattr(
        deger,
        "routes",
    ):
        print(
            "ROUTER_NESNESI",
            ad,
            type(deger).__name__,
            len(deger.routes),
        )

        for route in deger.routes:
            print(
                "  ROUTER_YOL",
                getattr(
                    route,
                    "path",
                    None,
                ),
            )

print()
print("=== TERMINAL ROUTES KAYNAK TANIMLARI ===")

for node in router_agac.body:
    if isinstance(
        node,
        (
            ast.Assign,
            ast.AnnAssign,
        ),
    ):
        print(
            "TANIM",
            node.lineno,
            ast.unparse(node),
        )

print()
print("=== ANA DOSYA IMPORTLARI ===")

for node in ana_agac.body:
    if isinstance(
        node,
        ast.ImportFrom,
    ):
        if (
            "terminal"
            in (node.module or "").casefold()
            or "finans"
            in (node.module or "").casefold()
        ):
            print(
                "IMPORT",
                node.lineno,
                ast.unparse(node),
            )

print()
print("=== UYGULAMA_OLUSTUR KAYNAGI ===")

print(
    inspect.getsource(
        uygulama_olustur
    )
)

print()
print("=== OLUSTURULAN UYGULAMA YOLLARI ===")

uygulama = uygulama_olustur(
    hesap_deposu_etkin=False
)

for route in uygulama.routes:
    yol = getattr(
        route,
        "path",
        None,
    )

    if yol:
        print(
            "APP_YOL",
            yol,
        )

print()
print("=== HEDEF SAYIMLARI ===")

hedefler = (
    "/api/syk-ui/terminal/state",
    "/syfinans/runtime",
)

yollar = tuple(
    getattr(
        route,
        "path",
        "",
    )
    for route in uygulama.routes
)

for hedef in hedefler:
    print(
        "HEDEF",
        hedef,
        "SAYI",
        yollar.count(hedef),
    )

print()
print("TERMINAL_ROUTER_KESIN_TESHIS_OK")