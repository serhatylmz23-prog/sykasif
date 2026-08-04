from __future__ import annotations

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import app

from syk_simulasyon.syk_ui_runtime.api_routes import (
    router as syk_ui_router,
)


beklenen_ui = (
    "/api/syk-ui/jarmin/integration",
    "/api/syk-ui/mobile-runtime",
    "/api/syk-ui/mobile-sensors",
    "/api/syk-ui/mobile-offline",
    "/api/syk-ui/mobile-control",
    "/api/syk-ui/kasif-icons",
)

beklenen_app = (
    *beklenen_ui,
    "/syfinans/runtime",
)


def yol_listesi(
    nesne,
) -> tuple[str, ...]:
    return tuple(
        route.path
        for route in nesne.routes
        if getattr(
            route,
            "path",
            None,
        )
    )


ui_yollari = yol_listesi(
    syk_ui_router
)

app_yollari = yol_listesi(
    app
)


print(
    "=== UI ROUTER YOLLARI ==="
)

eksik_ui = []

for beklenen in beklenen_ui:
    bulundu = any(
        yol == beklenen
        or yol.startswith(
            beklenen.rstrip("/") + "/"
        )
        for yol in ui_yollari
    )

    print(
        "UI_YOL",
        beklenen,
        "VAR" if bulundu else "YOK",
    )

    if not bulundu:
        eksik_ui.append(
            beklenen
        )

if eksik_ui:
    raise RuntimeError(
        "UI router eksik yolları: "
        + ", ".join(
            eksik_ui
        )
    )


print()
print(
    "=== GERÇEK APP YOLLARI ==="
)

eksik_app = []

for beklenen in beklenen_app:
    bulundu = any(
        yol == beklenen
        or yol.startswith(
            beklenen.rstrip("/") + "/"
        )
        for yol in app_yollari
    )

    print(
        "APP_YOL",
        beklenen,
        "VAR" if bulundu else "YOK",
    )

    if not bulundu:
        eksik_app.append(
            beklenen
        )

if eksik_app:
    raise RuntimeError(
        "Gerçek app eksik yolları: "
        + ", ".join(
            eksik_app
        )
    )


yinelenenler = sorted(
    {
        yol
        for yol in app_yollari
        if app_yollari.count(
            yol
        ) > 1
        and any(
            ifade in yol.casefold()
            for ifade in (
                "jarmin",
                "mobile",
                "kasif",
                "finans",
            )
        )
    }
)

if yinelenenler:
    raise RuntimeError(
        "Yinelenen yollar: "
        + ", ".join(
            yinelenenler
        )
    )


istemci = TestClient(
    app
)

finans = istemci.get(
    "/syfinans/runtime"
)

if finans.status_code != 200:
    raise RuntimeError(
        "SyFinans HTTP durumu: "
        f"{finans.status_code}"
    )


print()
print(
    "UI_ROUTER_YOL_SAYISI",
    len(
        ui_yollari
    ),
)

print(
    "APP_YOL_SAYISI",
    len(
        app_yollari
    ),
)

print(
    "SYFINANS_HTTP",
    finans.status_code,
)

print(
    "YINELENEN_YOL",
    len(
        yinelenenler
    ),
)

print(
    "SYK_ROUTER_ZINCIRI_KESIN_DOGRULANDI"
)