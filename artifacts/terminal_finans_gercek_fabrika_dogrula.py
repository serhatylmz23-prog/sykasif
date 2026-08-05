from __future__ import annotations

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)


uygulama = uygulama_olustur(
    hesap_deposu_etkin=False
)

istemci = TestClient(
    uygulama
)

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
    sayi = yollar.count(
        hedef
    )

    print(
        "ROUTE",
        hedef,
        "SAYI",
        sayi,
    )

    if hedef == "/syfinans/runtime" and sayi == 0:
        print(
            "SYFINANS_ROUTE_ATLANDI"
        )
        continue

    if sayi != 1:
        raise RuntimeError(
            f"Yol tekil degil: {hedef}={sayi}"
        )

    yanit = istemci.get(
        hedef
    )

    print(
        "HTTP",
        hedef,
        yanit.status_code,
    )

    if yanit.status_code != 200:
        raise RuntimeError(
            f"HTTP basarisiz: "
            f"{hedef}={yanit.status_code}"
        )

terminal = istemci.get(
    "/api/syk-ui/terminal/state"
).json()

if terminal["terminal_id"] != "syk-main-terminal":
    raise RuntimeError(
        "Terminal kimligi hatali."
    )

if len(
    terminal["modules"]
) != 9:
    raise RuntimeError(
        "Terminal modul sayisi hatali."
    )

print(
    "TERMINAL_FINANS_CANLI_HTTP_OK"
)