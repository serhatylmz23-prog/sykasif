from __future__ import annotations

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)


uygulama = uygulama_olustur(
    hesap_deposu_etkin=False
)

hedefler = (
    "/api/syk-ui/terminal/state",
    "/syfinans/runtime",
)

yollar = tuple(
    getattr(route, "path", "")
    for route in uygulama.router.routes
)

print(
    "APP_ROUTE_SAYISI",
    len(uygulama.routes),
)

print(
    "ROUTER_ROUTE_SAYISI",
    len(uygulama.router.routes),
)

for hedef in hedefler:
    sayi = yollar.count(hedef)

    print(
        "ROUTE",
        hedef,
        "SAYI",
        sayi,
    )

    if sayi != 1:
        raise RuntimeError(
            f"Yol tekil değil: {hedef}={sayi}"
        )

istemci = TestClient(
    uygulama
)

for hedef in hedefler:
    yanit = istemci.get(hedef)

    print(
        "HTTP",
        hedef,
        yanit.status_code,
    )

    if yanit.status_code != 200:
        raise RuntimeError(
            f"HTTP başarısız: "
            f"{hedef}={yanit.status_code}"
        )

terminal = istemci.get(
    "/api/syk-ui/terminal/state"
).json()

if terminal["terminal_id"] != "syk-main-terminal":
    raise RuntimeError(
        "Terminal kimliği hatalı."
    )

if len(terminal["modules"]) != 9:
    raise RuntimeError(
        "Terminal modül sayısı hatalı."
    )

finans = istemci.get(
    "/syfinans/runtime"
).json()

if not finans:
    raise RuntimeError(
        "SyFinans runtime yanıtı boş."
    )

print(
    "TERMINAL_FINANS_CANLI_HTTP_OK"
)