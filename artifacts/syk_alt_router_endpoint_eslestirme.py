from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

from syk_simulasyon.runtime_ui_sunucusu import app

from syk_simulasyon.syk_ui_runtime.api_routes import (
    router as syk_ui_router,
)


RAPOR_JSON = Path(
    "artifacts/"
    "SYK_ALT_ROUTER_ENDPOINT_ESLESTIRME.json"
)

RAPOR_TXT = Path(
    "artifacts/"
    "SYK_ALT_ROUTER_ENDPOINT_ESLESTIRME.txt"
)


ROUTERLAR = (
    (
        "mobile_control",
        (
            "syk_simulasyon.syk_ui_runtime."
            "mobile_control_routes"
        ),
        "router",
    ),
    (
        "mobile_device",
        (
            "syk_simulasyon.syk_ui_runtime."
            "mobile_device_routes"
        ),
        "router",
    ),
    (
        "mobile_offline",
        (
            "syk_simulasyon.syk_ui_runtime."
            "mobile_offline_routes"
        ),
        "router",
    ),
    (
        "mobile_sensor",
        (
            "syk_simulasyon.syk_ui_runtime."
            "mobile_sensor_routes"
        ),
        "router",
    ),
    (
        "kasif_icon",
        (
            "syk_simulasyon.syk_ui_runtime."
            "kasif_icon_routes"
        ),
        "router",
    ),
    (
        "jarmin",
        "syk_jarmin.jarmin_integration_api",
        "router",
    ),
)


def route_kayitlari(
    nesne: Any,
) -> list[dict[str, Any]]:
    kayitlar = []

    for route in getattr(
        nesne,
        "routes",
        (),
    ):
        yol = getattr(
            route,
            "path",
            None,
        )

        if not yol:
            continue

        kayitlar.append(
            {
                "path": str(yol),
                "name": getattr(
                    route,
                    "name",
                    None,
                ),
                "methods": sorted(
                    getattr(
                        route,
                        "methods",
                        (),
                    )
                    or ()
                ),
            }
        )

    return sorted(
        kayitlar,
        key=lambda kayit: (
            kayit["path"],
            kayit["methods"],
        ),
    )


alt_routerlar = []

for kisa_ad, modul_adi, nesne_adi in ROUTERLAR:
    modul = importlib.import_module(
        modul_adi
    )

    router = getattr(
        modul,
        nesne_adi
    )

    kayitlar = route_kayitlari(
        router
    )

    alt_routerlar.append(
        {
            "kisa_ad": kisa_ad,
            "modul": modul_adi,
            "nesne": nesne_adi,
            "prefix": getattr(
                router,
                "prefix",
                "",
            ),
            "route_sayisi": len(
                kayitlar
            ),
            "routes": kayitlar,
        }
    )


ui_routes = route_kayitlari(
    syk_ui_router
)

app_routes = route_kayitlari(
    app
)


rapor_temeli = {
    "schema": (
        "syk-alt-router-endpoint-"
        "eslestirme/v1"
    ),
    "alt_routerlar": alt_routerlar,
    "ui_router": {
        "prefix": getattr(
            syk_ui_router,
            "prefix",
            "",
        ),
        "route_sayisi": len(
            ui_routes
        ),
        "routes": ui_routes,
    },
    "gercek_app": {
        "route_sayisi": len(
            app_routes
        ),
        "routes": app_routes,
    },
}

rapor_sha256 = sha256(
    json.dumps(
        rapor_temeli,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()

rapor = {
    **rapor_temeli,
    "rapor_sha256": rapor_sha256,
}

RAPOR_JSON.write_text(
    json.dumps(
        rapor,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)


satirlar = [
    "SYK ALT ROUTER ENDPOINT EŞLEŞTİRME",
    "",
]

for router in alt_routerlar:
    satirlar.extend(
        [
            (
                f"ROUTER: {router['kisa_ad']}"
            ),
            (
                f"MODÜL: {router['modul']}"
            ),
            (
                f"PREFIX: {router['prefix']}"
            ),
            (
                "ROUTE SAYISI: "
                f"{router['route_sayisi']}"
            ),
        ]
    )

    if not router["routes"]:
        satirlar.append(
            "  ROUTE BULUNAMADI"
        )
    else:
        for route in router["routes"]:
            satirlar.append(
                (
                    "  "
                    + ",".join(
                        route["methods"]
                    )
                    + " "
                    + route["path"]
                    + " | "
                    + str(
                        route["name"]
                    )
                )
            )

    satirlar.append("")


satirlar.extend(
    [
        "SYK UI ROUTER GERÇEK YOLLARI",
        (
            "PREFIX: "
            f"{rapor['ui_router']['prefix']}"
        ),
        (
            "ROUTE SAYISI: "
            f"{rapor['ui_router']['route_sayisi']}"
        ),
    ]
)

for route in ui_routes:
    if any(
        ifade in route["path"].casefold()
        for ifade in (
            "mobile",
            "jarmin",
            "kasif",
        )
    ):
        satirlar.append(
            (
                "  "
                + ",".join(
                    route["methods"]
                )
                + " "
                + route["path"]
            )
        )


satirlar.extend(
    [
        "",
        "GERÇEK APP İLGİLİ YOLLARI",
        (
            "ROUTE SAYISI: "
            f"{rapor['gercek_app']['route_sayisi']}"
        ),
    ]
)

for route in app_routes:
    if any(
        ifade in route["path"].casefold()
        for ifade in (
            "syk-ui",
            "mobile",
            "jarmin",
            "kasif",
            "finans",
        )
    ):
        satirlar.append(
            (
                "  "
                + ",".join(
                    route["methods"]
                )
                + " "
                + route["path"]
            )
        )


satirlar.extend(
    [
        "",
        (
            "RAPOR SHA-256: "
            f"{rapor_sha256}"
        ),
    ]
)

RAPOR_TXT.write_text(
    "\n".join(
        satirlar
    )
    + "\n",
    encoding="utf-8",
)


print(
    "SYK_ALT_ROUTER_ENDPOINT_ESLESTIRME_OK"
)

for router in alt_routerlar:
    print(
        "ROUTER",
        router["kisa_ad"],
        "PREFIX",
        router["prefix"],
        "YOL",
        router["route_sayisi"],
    )

    for route in router["routes"]:
        print(
            "  ENDPOINT",
            route["path"],
            "METHOD",
            ",".join(
                route["methods"]
            ),
        )

print(
    "UI_ROUTER_TOPLAM_YOL",
    len(
        ui_routes
    ),
)

print(
    "GERCEK_APP_TOPLAM_YOL",
    len(
        app_routes
    ),
)

print(
    "RAPOR",
    RAPOR_TXT,
)