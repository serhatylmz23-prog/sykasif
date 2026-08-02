from __future__ import annotations

from fastapi import FastAPI

from . import runtime_fastapi_sunucusu as mevcut_sunucu
from .syk_ui import install_ui


def _mevcut_uygulamayi_bul() -> FastAPI:
    for ad in ("app", "uygulama"):
        aday = getattr(mevcut_sunucu, ad, None)
        if isinstance(aday, FastAPI):
            return aday

    for ad in (
        "uygulama_olustur",
        "create_app",
        "sunucu_olustur",
    ):
        fabrika = getattr(mevcut_sunucu, ad, None)
        if callable(fabrika):
            aday = fabrika()
            if isinstance(aday, FastAPI):
                return aday

    raise RuntimeError(
        "Mevcut FastAPI uygulaması veya uygulama fabrikası bulunamadı."
    )


def _ui_kurulu_mu(uygulama: FastAPI) -> bool:
    yollar = {
        getattr(route, "path", None)
        for route in uygulama.routes
    }
    return (
        "/syk-ui-screen" in yollar
        and "/api/syk-ui/runtime-state" in yollar
    )


app = _mevcut_uygulamayi_bul()

if not _ui_kurulu_mu(app):
    install_ui(app)