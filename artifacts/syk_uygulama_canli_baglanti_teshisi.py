from __future__ import annotations

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import app
from syk_simulasyon.syk_ui_runtime.api_routes import (
    router as syk_ui_router,
)
from syk_simulasyon.syk_ui_runtime.syfinans_runtime_routes import (
    finans_router,
)


def yollar(nesne) -> tuple[str, ...]:
    return tuple(
        str(route.path)
        for route in nesne.routes
        if getattr(route, "path", None)
    )


def kok_var(
    mevcut_yollar: tuple[str, ...],
    kok: str,
) -> bool:
    return any(
        yol == kok
        or yol.startswith(
            kok.rstrip("/") + "/"
        )
        for yol in mevcut_yollar
    )


once = yollar(app)
ui = yollar(syk_ui_router)
finans = yollar(finans_router)

print("APP_ONCE", len(once))
print("UI_ROUTER", len(ui))
print("FINANS_ROUTER", len(finans))

if not kok_var(
    once,
    "/api/syk-ui/mobile-runtime",
):
    app.include_router(
        syk_ui_router
    )

ara = yollar(app)

if not kok_var(
    ara,
    "/syfinans/runtime",
):
    app.include_router(
        finans_router
    )

sonra = yollar(app)

beklenenler = (
    "/api/syk-ui/jarmin/integration",
    "/api/syk-ui/mobile-runtime",
    "/api/syk-ui/mobile-sensors",
    "/api/syk-ui/mobile-offline",
    "/api/syk-ui/mobile-control",
    "/api/syk-ui/kasif-icons",
    "/syfinans/runtime",
)

eksikler = []

for beklenen in beklenenler:
    eslesenler = sorted(
        yol
        for yol in sonra
        if (
            yol == beklenen
            or yol.startswith(
                beklenen.rstrip("/") + "/"
            )
        )
    )

    print(
        "YOL",
        beklenen,
        "VAR" if eslesenler else "YOK",
    )

    for yol in eslesenler:
        print("  ESLESEN", yol)

    if not eslesenler:
        eksikler.append(beklenen)

print("APP_SONRA", len(sonra))
print("EKLENEN_YOL", len(sonra) - len(once))

istemci = TestClient(app)

finans_yaniti = istemci.get(
    "/syfinans/runtime"
)

print(
    "SYFINANS_HTTP",
    finans_yaniti.status_code,
)

if eksikler:
    raise RuntimeError(
        "Canlı bağlantı sonrasında eksik yollar: "
        + ", ".join(eksikler)
    )

if finans_yaniti.status_code != 200:
    raise RuntimeError(
        "SyFinans HTTP yanıtı başarısız: "
        f"{finans_yaniti.status_code}"
    )

print("CANLI_INCLUDE_ROUTER_DOGRULANDI")