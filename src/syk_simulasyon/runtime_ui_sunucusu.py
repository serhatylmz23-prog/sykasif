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
        "Mevcut FastAPI uygulamasÄ± veya uygulama fabrikasÄ± bulunamadÄ±."
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

# === SYK_GERCEK_APP_KESIN_BAGLANTI_BASLANGIC ===

from syk_simulasyon.syk_ui_runtime.api_routes import (
    router as syk_ui_router,
)

from syk_simulasyon.syk_ui_runtime.syfinans_runtime_routes import (
    finans_router,
)


def _syk_uygulama_yolu_var(
    yol: str,
) -> bool:
    return any(
        str(
            getattr(
                kayit,
                "path",
                "",
            )
        ) == yol
        or str(
            getattr(
                kayit,
                "path",
                "",
            )
        ).startswith(
            yol.rstrip("/") + "/"
        )
        for kayit in app.routes
    )


if not _syk_uygulama_yolu_var(
    "/api/syk-ui/mobile-runtime"
):
    app.include_router(
        syk_ui_router
    )


if not _syk_uygulama_yolu_var(
    "/syfinans/runtime"
):
    app.include_router(
        finans_router
    )

# === SYK_GERCEK_APP_KESIN_BAGLANTI_BITIS ===


if not _ui_kurulu_mu(app):
    install_ui(app)

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

# SYK_PROJECT_RUNTIME_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.project_routes import (
    project_router as syk_project_router,
)

_syk_project_route_paths = {
    getattr(route, "path", None)
    for route in syk_project_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_project_route_paths
]

_syk_project_insert_index = len(
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
        and (
            _syk_path.startswith("/api/syk-ui/")
            or _syk_path.startswith("/{")
        )
    ):
        _syk_project_insert_index = _syk_index
        break

for _syk_project_route in reversed(
    syk_project_router.routes
):
    app.router.routes.insert(
        _syk_project_insert_index,
        _syk_project_route,
    )
