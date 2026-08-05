from __future__ import annotations

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import app


hedef = "/api/syk-ui/terminal/state"

eslesenler = [
    route
    for route in app.routes
    if getattr(
        route,
        "path",
        None,
    )
    == hedef
]

print(
    "TERMINAL_ROUTE_SAYISI",
    len(eslesenler),
)

if len(eslesenler) != 1:
    raise RuntimeError(
        "Terminal yolu tekil degil: "
        f"{len(eslesenler)}"
    )

istemci = TestClient(app)

yanit = istemci.get(
    hedef
)

print(
    "TERMINAL_HTTP_DURUM",
    yanit.status_code,
)

if yanit.status_code != 200:
    raise RuntimeError(
        "Terminal HTTP yaniti basarisiz: "
        f"{yanit.status_code}"
    )

veri = yanit.json()

beklenen_moduller = (
    "projects",
    "research",
    "kasif",
    "map",
    "evidence",
    "reports",
    "devices",
    "notifications",
    "institute",
)

mevcut_moduller = tuple(
    oge["key"]
    for oge in veri["modules"]
)

if mevcut_moduller != beklenen_moduller:
    raise RuntimeError(
        "Terminal modul sirasi hatali: "
        f"{mevcut_moduller}"
    )

print(
    "TERMINAL_CANLI_HTTP_DOGRULANDI"
)