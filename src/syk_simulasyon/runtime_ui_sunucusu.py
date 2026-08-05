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

# SYK_MAP_WORKSPACE_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.map_workspace_routes import (
    map_workspace_router as syk_map_workspace_router,
)

_syk_map_paths = {
    getattr(route, "path", None)
    for route in syk_map_workspace_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_map_paths
]

_syk_map_insert_index = len(
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
        _syk_map_insert_index = _syk_index
        break

for _syk_map_route in reversed(
    syk_map_workspace_router.routes
):
    app.router.routes.insert(
        _syk_map_insert_index,
        _syk_map_route,
    )

# SYK_EXTERNAL_DEVICE_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.external_device_routes import (
    external_device_router as syk_external_device_router,
)

_syk_external_device_paths = {
    getattr(route, "path", None)
    for route in syk_external_device_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_external_device_paths
]

_syk_external_device_insert_index = len(
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
        and _syk_path.startswith(
            "/api/syk-ui/"
        )
    ):
        _syk_external_device_insert_index = (
            _syk_index
        )
        break

for _syk_external_device_route in reversed(
    syk_external_device_router.routes
):
    app.router.routes.insert(
        _syk_external_device_insert_index,
        _syk_external_device_route,
    )

# SYK_SONAR_SESSION_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.sonar_session_routes import (
    sonar_session_router as syk_sonar_session_router,
)

_syk_sonar_session_paths = {
    getattr(route, "path", None)
    for route in syk_sonar_session_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_sonar_session_paths
]

_syk_sonar_session_insert_index = len(
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
        and _syk_path.startswith(
            "/api/syk-ui/"
        )
    ):
        _syk_sonar_session_insert_index = (
            _syk_index
        )
        break

for _syk_sonar_session_route in reversed(
    syk_sonar_session_router.routes
):
    app.router.routes.insert(
        _syk_sonar_session_insert_index,
        _syk_sonar_session_route,
    )

# SYK_REAL_DEVICE_CONNECTION_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.real_device_connection_routes import (
    real_device_connection_router as syk_real_device_connection_router,
)

_syk_real_device_paths = {
    getattr(route, "path", None)
    for route in syk_real_device_connection_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_real_device_paths
]

_syk_real_device_insert_index = len(
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
        _syk_real_device_insert_index = _syk_index
        break

for _syk_real_device_route in reversed(
    syk_real_device_connection_router.routes
):
    app.router.routes.insert(
        _syk_real_device_insert_index,
        _syk_real_device_route,
    )

# SYK_SENSOR_GATEWAY_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.sensor_gateway_routes import (
    sensor_gateway_router as syk_sensor_gateway_router,
)

_syk_sensor_gateway_paths = {
    getattr(route, "path", None)
    for route in syk_sensor_gateway_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_sensor_gateway_paths
]

_syk_sensor_gateway_insert_index = len(
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
        and _syk_path.startswith(
            "/api/syk-ui/"
        )
    ):
        _syk_sensor_gateway_insert_index = (
            _syk_index
        )
        break

for _syk_sensor_gateway_route in reversed(
    syk_sensor_gateway_router.routes
):
    app.router.routes.insert(
        _syk_sensor_gateway_insert_index,
        _syk_sensor_gateway_route,
    )

# SYK_SENSOR_GATEWAY_SESSION_ROUTER_BAGLANTISI
from syk_simulasyon.syk_ui_runtime.sensor_gateway_session_routes import (
    sensor_gateway_session_router as syk_sensor_gateway_session_router,
)

_syk_sensor_session_paths = {
    getattr(route, "path", None)
    for route in syk_sensor_gateway_session_router.routes
}

app.router.routes[:] = [
    route
    for route in app.router.routes
    if getattr(route, "path", None)
    not in _syk_sensor_session_paths
]

_syk_sensor_session_insert_index = len(
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
        and _syk_path.startswith(
            "/api/syk-ui/"
        )
    ):
        _syk_sensor_session_insert_index = (
            _syk_index
        )
        break

for _syk_sensor_session_route in reversed(
    syk_sensor_gateway_session_router.routes
):
    app.router.routes.insert(
        _syk_sensor_session_insert_index,
        _syk_sensor_session_route,
    )
