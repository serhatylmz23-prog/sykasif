from __future__ import annotations

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)

from syk_simulasyon.syk_ui_runtime.api_routes import (
    router as syk_ui_router,
)


beklenen_ui_yollari = (
    "/api/syk-ui/jarmin/integration",
    "/api/syk-ui/mobile-runtime",
    "/api/syk-ui/mobile-sensors",
    "/api/syk-ui/mobile-offline",
    "/api/syk-ui/mobile-control",
    "/api/syk-ui/kasif-icons",
)

beklenen_app_yollari = (
    *beklenen_ui_yollari,
    "/syfinans/runtime",
)


def yollar(
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


ui_yollari = yollar(
    syk_ui_router
)

app_yollari = yollar(
    app
)


print(
    "=== SYK UI ROUTER ==="
)

ui_eksikleri = []

for beklenen in beklenen_ui_yollari:
    eslesen = sorted(
        yol
        for yol in ui_yollari
        if (
            yol == beklenen
            or yol.startswith(
                beklenen.rstrip("/")
                + "/"
            )
        )
    )

    print(
        "UI_YOL",
        beklenen,
        "VAR" if eslesen else "YOK",
    )

    if not eslesen:
        ui_eksikleri.append(
            beklenen
        )


if ui_eksikleri:
    raise RuntimeError(
        "SYK UI router eksik yolları: "
        + ", ".join(
            ui_eksikleri
        )
    )


print()
print(
    "=== GERÇEK FASTAPI APP ==="
)

app_eksikleri = []

for beklenen in beklenen_app_yollari:
    eslesen = sorted(
        yol
        for yol in app_yollari
        if (
            yol == beklenen
            or yol.startswith(
                beklenen.rstrip("/")
                + "/"
            )
        )
    )

    print(
        "APP_YOL",
        beklenen,
        "VAR" if eslesen else "YOK",
    )

    if not eslesen:
        app_eksikleri.append(
            beklenen
        )


if app_eksikleri:
    print()
    print(
        "APP_ICINDEKI_ILGILI_YOLLAR"
    )

    for yol in sorted(
        set(
            yol
            for yol in app_yollari
            if any(
                ifade in yol.casefold()
                for ifade in (
                    "syk-ui",
                    "mobile",
                    "jarmin",
                    "kasif",
                    "finans",
                )
            )
        )
    ):
        print(
            " ",
            yol,
        )

    raise RuntimeError(
        "Gerçek app eksik yolları: "
        + ", ".join(
            app_eksikleri
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
        "SyFinans HTTP yanıtı: "
        f"{finans.status_code}"
    )


print()
print(
    "SYK_UI_ROUTER_YOL_SAYISI",
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
    "SYK_ALT_ROUTER_ZINCIRI_DOGRULANDI"
)