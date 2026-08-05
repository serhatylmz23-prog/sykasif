from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI

import syk_simulasyon.runtime_fastapi_sunucusu as sunucu_modulu
from syk_simulasyon.syk_ui_runtime.syfinans_runtime_routes import (
    finans_router,
)
from syk_simulasyon.syk_ui_runtime.terminal_routes import (
    terminal_router,
)


rapor: list[str] = []


def yaz(*parcalar: Any) -> None:
    metin = " ".join(
        str(parca)
        for parca in parcalar
    )
    print(metin)
    rapor.append(metin)


def yollar(nesne: Any) -> tuple[str, ...]:
    return tuple(
        getattr(route, "path", "")
        for route in nesne.routes
    )


asil_fastapi_include = FastAPI.include_router
asil_apirouter_include = APIRouter.include_router


def fastapi_include_izle(
    self: FastAPI,
    router: APIRouter,
    *args: Any,
    **kwargs: Any,
) -> Any:
    yaz()
    yaz("FASTAPI_INCLUDE_BASLADI")
    yaz("APP_ID", id(self))
    yaz("APP_ROUTER_ID", id(self.router))
    yaz("APP_ROUTES_ID", id(self.router.routes))
    yaz("APP_ONCE", len(self.router.routes))
    yaz("KAYNAK_ROUTER_ID", id(router))
    yaz("KAYNAK_ROUTE_SAYISI", len(router.routes))
    yaz("KAYNAK_YOLLAR", yollar(router))

    sonuc = asil_fastapi_include(
        self,
        router,
        *args,
        **kwargs,
    )

    yaz("APP_SONRA", len(self.router.routes))
    yaz("APP_SONRA_YOLLAR", yollar(self.router))
    yaz("FASTAPI_INCLUDE_BITTI")

    return sonuc


def apirouter_include_izle(
    self: APIRouter,
    router: APIRouter,
    *args: Any,
    **kwargs: Any,
) -> Any:
    yaz()
    yaz("APIROUTER_INCLUDE_BASLADI")
    yaz("HEDEF_ROUTER_ID", id(self))
    yaz("HEDEF_ROUTES_ID", id(self.routes))
    yaz("HEDEF_ONCE", len(self.routes))
    yaz("KAYNAK_ROUTER_ID", id(router))
    yaz("KAYNAK_ROUTE_SAYISI", len(router.routes))
    yaz("KAYNAK_YOLLAR", yollar(router))

    sonuc = asil_apirouter_include(
        self,
        router,
        *args,
        **kwargs,
    )

    yaz("HEDEF_SONRA", len(self.routes))
    yaz("HEDEF_SONRA_YOLLAR", yollar(self))
    yaz("APIROUTER_INCLUDE_BITTI")

    return sonuc


FastAPI.include_router = fastapi_include_izle
APIRouter.include_router = apirouter_include_izle

try:
    yaz("=" * 72)
    yaz("TEMIZ_FASTAPI_KONTROLU")
    yaz("=" * 72)

    temiz = FastAPI()

    yaz("TEMIZ_APP_ID", id(temiz))
    yaz("TEMIZ_ROUTER_ID", id(temiz.router))
    yaz("TEMIZ_BASLANGIC", len(temiz.router.routes))

    temiz.include_router(
        terminal_router
    )
    temiz.include_router(
        finans_router
    )

    temiz_yollar = yollar(
        temiz.router
    )

    yaz("TEMIZ_SON_ROUTE_SAYISI", len(temiz_yollar))
    yaz(
        "TEMIZ_TERMINAL_SAYI",
        temiz_yollar.count(
            "/api/syk-ui/terminal/state"
        ),
    )
    yaz(
        "TEMIZ_FINANS_SAYI",
        temiz_yollar.count(
            "/syfinans/runtime"
        ),
    )

    yaz()
    yaz("=" * 72)
    yaz("GERCEK_UYGULAMA_KONTROLU")
    yaz("=" * 72)

    uygulama = sunucu_modulu.uygulama_olustur(
        hesap_deposu_etkin=False
    )

    gercek_yollar = yollar(
        uygulama.router
    )

    yaz("GERCEK_APP_ID", id(uygulama))
    yaz("GERCEK_ROUTER_ID", id(uygulama.router))
    yaz("GERCEK_ROUTES_ID", id(uygulama.router.routes))
    yaz("GERCEK_ROUTE_SAYISI", len(gercek_yollar))
    yaz(
        "GERCEK_TERMINAL_SAYI",
        gercek_yollar.count(
            "/api/syk-ui/terminal/state"
        ),
    )
    yaz(
        "GERCEK_FINANS_SAYI",
        gercek_yollar.count(
            "/syfinans/runtime"
        ),
    )

    yaz()
    yaz("=" * 72)
    yaz("DOGRUDAN_APPEND_KONTROLU")
    yaz("=" * 72)

    once = len(
        uygulama.router.routes
    )

    terminal_ilk_route = terminal_router.routes[0]

    uygulama.router.routes.append(
        terminal_ilk_route
    )

    sonra = len(
        uygulama.router.routes
    )

    yaz("APPEND_ONCE", once)
    yaz("APPEND_SONRA", sonra)
    yaz(
        "APPEND_AYNI_LISTE",
        uygulama.routes is uygulama.router.routes,
    )
    yaz(
        "APPEND_TERMINAL_SAYI",
        yollar(
            uygulama.router
        ).count(
            "/api/syk-ui/terminal/state"
        ),
    )

    if sonra != once + 1:
        raise RuntimeError(
            "APIRouter route listesi append sonrasinda degismedi."
        )

    yaz()
    yaz("SYK_DSP_0012_ROUTE_MUTASYON_TESHISI_OK")

finally:
    FastAPI.include_router = asil_fastapi_include
    APIRouter.include_router = asil_apirouter_include

    Path(
        "artifacts/SYK_DSP_0012_ROUTE_MUTASYON_TESHISI.txt"
    ).write_text(
        "\n".join(rapor) + "\n",
        encoding="utf-8",
    )