from __future__ import annotations

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import (
    RuntimeFastApiSunucusu,
)


sunucu = RuntimeFastApiSunucusu.__new__(
    RuntimeFastApiSunucusu
)

sunucu._api = None
sunucu._websocket = None
sunucu._terminal = None
sunucu._runtime_servisi = None
sunucu._oturum_yoneticisi = None
sunucu._hesap_deposu = None

uygulama = sunucu.olustur()

hedef = "/api/syk-ui/terminal/state"

eslesenler = [
    route
    for route in uygulama.routes
    if getattr(
        route,
        "path",
        None,
    )
    == hedef
]

print(
    "ROUTE_SAYISI",
    len(eslesenler),
)

if len(eslesenler) != 1:
    raise RuntimeError(
        "Terminal yolu tekil degil: "
        f"{len(eslesenler)}"
    )

istemci = TestClient(
    uygulama
)

yanit = istemci.get(
    hedef
)

print(
    "HTTP_DURUM",
    yanit.status_code,
)

if yanit.status_code != 200:
    raise RuntimeError(
        "Terminal HTTP yaniti basarisiz."
    )

veri = yanit.json()

if veri["terminal_id"] != "syk-main-terminal":
    raise RuntimeError(
        "Terminal kimligi hatali."
    )

if len(veri["modules"]) != 9:
    raise RuntimeError(
        "Terminal modul sayisi hatali."
    )

print(
    "TERMINAL_FASTAPI_FABRIKA_CANLI_HTTP_OK"
)