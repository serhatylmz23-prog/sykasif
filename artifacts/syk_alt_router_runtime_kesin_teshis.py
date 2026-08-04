from __future__ import annotations

import ast
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter


API_YOLU = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/api_routes.py"
)

RAPOR_JSON = Path(
    "artifacts/"
    "SYK_ALT_ROUTER_RUNTIME_KESIN_TESHIS.json"
)

RAPOR_TXT = Path(
    "artifacts/"
    "SYK_ALT_ROUTER_RUNTIME_KESIN_TESHIS.txt"
)


MODULLER = (
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


def yol_listesi(
    router: Any,
) -> list[str]:
    return [
        str(
            route.path
        )
        for route in getattr(
            router,
            "routes",
            ()
        )
        if getattr(
            route,
            "path",
            None,
        )
    ]


def ifade_adi(
    dugum: ast.AST | None,
) -> str:
    if dugum is None:
        return ""

    if isinstance(
        dugum,
        ast.Name,
    ):
        return dugum.id

    if isinstance(
        dugum,
        ast.Attribute,
    ):
        onceki = ifade_adi(
            dugum.value
        )

        return (
            f"{onceki}.{dugum.attr}"
            if onceki
            else dugum.attr
        )

    return ""


def ebeveyn_haritasi(
    agac: ast.AST,
) -> dict[ast.AST, ast.AST]:
    return {
        cocuk: ebeveyn
        for ebeveyn in ast.walk(
            agac
        )
        for cocuk in ast.iter_child_nodes(
            ebeveyn
        )
    }


def kapsam(
    dugum: ast.AST,
    ebeveynler: dict[
        ast.AST,
        ast.AST,
    ],
) -> list[str]:
    sonuc = []
    mevcut = dugum

    while mevcut in ebeveynler:
        mevcut = ebeveynler[
            mevcut
        ]

        if isinstance(
            mevcut,
            ast.Module,
        ):
            sonuc.append(
                "module"
            )

        elif isinstance(
            mevcut,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            sonuc.append(
                f"function:{mevcut.name}"
            )

        elif isinstance(
            mevcut,
            ast.ClassDef,
        ):
            sonuc.append(
                f"class:{mevcut.name}"
            )

        elif isinstance(
            mevcut,
            ast.If,
        ):
            sonuc.append(
                "if"
            )

        elif isinstance(
            mevcut,
            ast.Try,
        ):
            sonuc.append(
                "try"
            )

    sonuc.reverse()

    return sonuc


kaynak = API_YOLU.read_text(
    encoding="utf-8",
)

agac = ast.parse(
    kaynak,
    filename=str(
        API_YOLU
    ),
)

ebeveynler = ebeveyn_haritasi(
    agac
)

include_kayitlari = []

for dugum in ast.walk(
    agac
):
    if not isinstance(
        dugum,
        ast.Call,
    ):
        continue

    cagri = ifade_adi(
        dugum.func
    )

    if not cagri.endswith(
        "include_router"
    ):
        continue

    include_kayitlari.append(
        {
            "satir": getattr(
                dugum,
                "lineno",
                0,
            ),
            "cagri": cagri,
            "router": (
                ifade_adi(
                    dugum.args[0]
                )
                if dugum.args
                else None
            ),
            "kapsam": kapsam(
                dugum,
                ebeveynler,
            ),
            "kaynak": ast.unparse(
                dugum
            ),
        }
    )


api_modulu = importlib.import_module(
    "syk_simulasyon.syk_ui_runtime."
    "api_routes"
)

ana_router = getattr(
    api_modulu,
    "router"
)

ana_router_yollari = yol_listesi(
    ana_router
)


alt_routerlar = []
router_nesneleri = []

for kisa_ad, modul_adi, nesne_adi in MODULLER:
    modul = importlib.import_module(
        modul_adi
    )

    router = getattr(
        modul,
        nesne_adi
    )

    yollar = yol_listesi(
        router
    )

    router_nesneleri.append(
        (
            kisa_ad,
            router,
        )
    )

    alt_routerlar.append(
        {
            "kisa_ad": kisa_ad,
            "modul": modul_adi,
            "nesne": nesne_adi,
            "router_id": id(
                router
            ),
            "prefix": getattr(
                router,
                "prefix",
                None,
            ),
            "yol_sayisi": len(
                yollar
            ),
            "yollar": yollar,
        }
    )


# Alt router'ları tamamen temiz bir deneme
# router'ına bağlayarak FastAPI'nin oluşturduğu
# gerçek birleşik yolları ölç.
deneme_router = APIRouter(
    prefix="/api/syk-ui"
)

deneme_hatalari = []

for kisa_ad, router in router_nesneleri:
    try:
        deneme_router.include_router(
            router
        )
    except Exception as error:
        deneme_hatalari.append(
            {
                "router": kisa_ad,
                "hata_turu": (
                    type(error).__name__
                ),
                "hata": str(
                    error
                ),
            }
        )

deneme_yollari = yol_listesi(
    deneme_router
)


beklenenler = (
    "/api/syk-ui/jarmin/integration",
    "/api/syk-ui/mobile-runtime",
    "/api/syk-ui/mobile-sensors",
    "/api/syk-ui/mobile-offline",
    "/api/syk-ui/mobile-control",
    "/api/syk-ui/kasif-icons",
)

beklenen_durumlari = []

for beklenen in beklenenler:
    ana_eslesme = sorted(
        yol
        for yol in ana_router_yollari
        if (
            yol == beklenen
            or yol.startswith(
                beklenen.rstrip("/") + "/"
            )
        )
    )

    deneme_eslesme = sorted(
        yol
        for yol in deneme_yollari
        if (
            yol == beklenen
            or yol.startswith(
                beklenen.rstrip("/") + "/"
            )
        )
    )

    beklenen_durumlari.append(
        {
            "beklenen": beklenen,
            "ana_router_eslesmeleri": (
                ana_eslesme
            ),
            "deneme_router_eslesmeleri": (
                deneme_eslesme
            ),
        }
    )


satirlar = kaynak.splitlines()

son_kaynak_satirlari = [
    {
        "satir": sira,
        "metin": satirlar[
            sira - 1
        ],
    }
    for sira in range(
        max(
            1,
            len(
                satirlar
            ) - 119,
        ),
        len(
            satirlar
        ) + 1,
    )
]


rapor_temeli = {
    "schema": (
        "syk-alt-router-runtime-"
        "kesin-teshis/v1"
    ),
    "api_routes": (
        API_YOLU.as_posix()
    ),
    "api_routes_sha256": sha256(
        kaynak.encode(
            "utf-8"
        )
    ).hexdigest(),
    "ana_router_id": id(
        ana_router
    ),
    "ana_router_prefix": getattr(
        ana_router,
        "prefix",
        None,
    ),
    "ana_router_yol_sayisi": len(
        ana_router_yollari
    ),
    "ana_router_yollari": (
        ana_router_yollari
    ),
    "alt_routerlar": alt_routerlar,
    "include_kayitlari": (
        include_kayitlari
    ),
    "deneme_router_prefix": getattr(
        deneme_router,
        "prefix",
        None,
    ),
    "deneme_router_yol_sayisi": len(
        deneme_yollari
    ),
    "deneme_router_yollari": (
        deneme_yollari
    ),
    "deneme_hatalari": (
        deneme_hatalari
    ),
    "beklenen_durumlari": (
        beklenen_durumlari
    ),
    "son_kaynak_satirlari": (
        son_kaynak_satirlari
    ),
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
    "rapor_sha256": (
        rapor_sha256
    ),
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


metin_raporu = [
    (
        "SYK ALT ROUTER RUNTIME "
        "KESİN TEŞHİS"
    ),
    "",
    (
        "ANA ROUTER PREFIX: "
        f"{rapor['ana_router_prefix']}"
    ),
    (
        "ANA ROUTER YOL SAYISI: "
        f"{rapor['ana_router_yol_sayisi']}"
    ),
    "",
    "ALT ROUTERLAR",
]

for kayit in alt_routerlar:
    metin_raporu.append(
        (
            f"{kayit['kisa_ad']} | "
            f"prefix={kayit['prefix']} | "
            f"yol={kayit['yol_sayisi']} | "
            f"id={kayit['router_id']}"
        )
    )

    for yol in kayit[
        "yollar"
    ]:
        metin_raporu.append(
            f"  {yol}"
        )


metin_raporu.extend(
    [
        "",
        "API_ROUTES INCLUDE KAYITLARI",
    ]
)

for kayit in include_kayitlari:
    metin_raporu.append(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


metin_raporu.extend(
    [
        "",
        (
            "DENEME ROUTER YOL SAYISI: "
            f"{len(deneme_yollari)}"
        ),
    ]
)

for yol in deneme_yollari:
    metin_raporu.append(
        yol
    )


metin_raporu.extend(
    [
        "",
        "BEKLENEN YOL KARŞILAŞTIRMASI",
    ]
)

for kayit in beklenen_durumlari:
    metin_raporu.append(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


metin_raporu.extend(
    [
        "",
        "API_ROUTES SON 120 SATIR",
    ]
)

for kayit in son_kaynak_satirlari:
    metin_raporu.append(
        (
            f"{kayit['satir']:>5} | "
            f"{kayit['metin']}"
        )
    )


metin_raporu.extend(
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
        metin_raporu
    )
    + "\n",
    encoding="utf-8",
)


print(
    "SYK_ALT_ROUTER_RUNTIME_"
    "KESIN_TESHIS_OK"
)

print(
    "ANA_ROUTER_PREFIX",
    rapor[
        "ana_router_prefix"
    ],
)

print(
    "ANA_ROUTER_YOLU",
    rapor[
        "ana_router_yol_sayisi"
    ],
)

for kayit in alt_routerlar:
    print(
        "ALT_ROUTER",
        kayit["kisa_ad"],
        "PREFIX",
        kayit["prefix"],
        "YOL",
        kayit["yol_sayisi"],
    )

print(
    "MODUL_SEVIYESI_INCLUDE",
    sum(
        kayit["kapsam"]
        == ["module"]
        for kayit
        in include_kayitlari
    ),
)

print(
    "TOPLAM_INCLUDE",
    len(
        include_kayitlari
    ),
)

print(
    "DENEME_ROUTER_YOLU",
    len(
        deneme_yollari
    ),
)

print(
    "DENEME_HATASI",
    len(
        deneme_hatalari
    ),
)

for kayit in beklenen_durumlari:
    print(
        "BEKLENEN",
        kayit["beklenen"],
        "ANA",
        (
            "VAR"
            if kayit[
                "ana_router_eslesmeleri"
            ]
            else "YOK"
        ),
        "DENEME",
        (
            "VAR"
            if kayit[
                "deneme_router_eslesmeleri"
            ]
            else "YOK"
        ),
    )

print(
    "RAPOR",
    RAPOR_TXT,
)