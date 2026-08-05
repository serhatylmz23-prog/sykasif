from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

import syk_simulasyon.runtime_fastapi_sunucusu as sunucu_modulu
from syk_simulasyon.syk_ui_runtime.terminal_routes import (
    terminal_router,
)
from syk_simulasyon.syk_ui_runtime.syfinans_runtime_routes import (
    finans_router,
)


print("SUNUCU_DOSYASI", Path(sunucu_modulu.__file__).resolve())

print("TERMINAL_ROUTER_YOLLARI")
for route in terminal_router.routes:
    print(" ", getattr(route, "path", None))

print("FINANS_ROUTER_YOLLARI")
for route in finans_router.routes:
    print(" ", getattr(route, "path", None))


asil_include_router = FastAPI.include_router


def kayitli_include_router(
    self,
    router,
    *args,
    **kwargs,
):
    print(
        "INCLUDE_ROUTER_CAGRILDI",
        tuple(
            getattr(route, "path", None)
            for route in router.routes
        ),
    )

    return asil_include_router(
        self,
        router,
        *args,
        **kwargs,
    )


FastAPI.include_router = kayitli_include_router

try:
    uygulama = sunucu_modulu.uygulama_olustur(
        hesap_deposu_etkin=False
    )
finally:
    FastAPI.include_router = asil_include_router


hedefler = (
    "/api/syk-ui/terminal/state",
    "/syfinans/runtime",
)

yollar = tuple(
    getattr(route, "path", "")
    for route in uygulama.routes
)

print("ILK_DURUM")

for hedef in hedefler:
    print(
        "HEDEF",
        hedef,
        "SAYI",
        yollar.count(hedef),
    )


if yollar.count("/api/syk-ui/terminal/state") == 0:
    uygulama.include_router(
        terminal_router
    )

if yollar.count("/syfinans/runtime") == 0:
    uygulama.include_router(
        finans_router
    )


son_yollar = tuple(
    getattr(route, "path", "")
    for route in uygulama.routes
)

print("ELLE_BAGLANTI_SONRASI")

for hedef in hedefler:
    sayi = son_yollar.count(hedef)

    print(
        "HEDEF",
        hedef,
        "SAYI",
        sayi,
    )

    if sayi != 1:
        raise RuntimeError(
            f"Router elle baglandiginda da tekil degil: "
            f"{hedef}={sayi}"
        )


print("TERMINAL_FINANS_CALISAN_KOD_YOLU_TESHISI_OK")