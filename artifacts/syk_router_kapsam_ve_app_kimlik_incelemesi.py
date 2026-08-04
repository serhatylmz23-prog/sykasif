from __future__ import annotations

import ast
from hashlib import sha256
import importlib
import inspect
import json
from pathlib import Path
from typing import Any


SUNUCU = Path(
    "src/syk_simulasyon/"
    "runtime_ui_sunucusu.py"
)

API_ROUTES = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/api_routes.py"
)

FINANS_ROUTES = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/syfinans_runtime_routes.py"
)

RAPOR_JSON = Path(
    "artifacts/"
    "SYK_ROUTER_KAPSAM_VE_APP_KIMLIK_INCELEMESI.json"
)

RAPOR_TXT = Path(
    "artifacts/"
    "SYK_ROUTER_KAPSAM_VE_APP_KIMLIK_INCELEMESI.txt"
)


def oku(
    yol: Path,
) -> str:
    return yol.read_text(
        encoding="utf-8",
        errors="replace",
    )


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

    if isinstance(
        dugum,
        ast.Call,
    ):
        return ifade_adi(
            dugum.func
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


def kapsam_zinciri(
    dugum: ast.AST,
    ebeveynler: dict[
        ast.AST,
        ast.AST,
    ],
) -> list[str]:
    zincir = []
    mevcut = dugum

    while mevcut in ebeveynler:
        mevcut = ebeveynler[
            mevcut
        ]

        if isinstance(
            mevcut,
            ast.Module,
        ):
            zincir.append(
                "module"
            )

        elif isinstance(
            mevcut,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            zincir.append(
                f"function:{mevcut.name}"
            )

        elif isinstance(
            mevcut,
            ast.ClassDef,
        ):
            zincir.append(
                f"class:{mevcut.name}"
            )

        elif isinstance(
            mevcut,
            ast.If,
        ):
            zincir.append(
                "if:"
                + ast.unparse(
                    mevcut.test
                )
            )

        elif isinstance(
            mevcut,
            ast.Try,
        ):
            zincir.append(
                "try"
            )

        elif isinstance(
            mevcut,
            ast.With,
        ):
            zincir.append(
                "with"
            )

    zincir.reverse()

    return zincir


def kaynak_kayitlari(
    yol: Path,
) -> dict[str, Any]:
    metin = oku(
        yol
    )

    agac = ast.parse(
        metin,
        filename=str(yol),
    )

    ebeveynler = ebeveyn_haritasi(
        agac
    )

    app_atamalari = []
    importlar = []
    include_routerlar = []

    for dugum in ast.walk(
        agac
    ):
        if isinstance(
            dugum,
            ast.ImportFrom,
        ):
            adlar = [
                {
                    "ad": ad.name,
                    "takma_ad": ad.asname,
                }
                for ad in dugum.names
            ]

            if any(
                (
                    ad["ad"]
                    in {
                        "router",
                        "finans_router",
                    }
                    or ad["takma_ad"]
                    in {
                        "syk_ui_router",
                        "finans_router",
                    }
                )
                for ad in adlar
            ):
                importlar.append(
                    {
                        "satir": dugum.lineno,
                        "modul": dugum.module,
                        "seviye": dugum.level,
                        "adlar": adlar,
                        "kapsam": kapsam_zinciri(
                            dugum,
                            ebeveynler,
                        ),
                    }
                )

        elif isinstance(
            dugum,
            ast.Assign,
        ):
            hedefler = [
                ifade_adi(
                    hedef
                )
                for hedef in dugum.targets
            ]

            if "app" in hedefler:
                app_atamalari.append(
                    {
                        "satir": dugum.lineno,
                        "hedefler": hedefler,
                        "deger": ifade_adi(
                            dugum.value
                        ),
                        "kaynak": ast.unparse(
                            dugum
                        ),
                        "kapsam": kapsam_zinciri(
                            dugum,
                            ebeveynler,
                        ),
                    }
                )

        elif isinstance(
            dugum,
            ast.AnnAssign,
        ):
            if ifade_adi(
                dugum.target
            ) == "app":
                app_atamalari.append(
                    {
                        "satir": dugum.lineno,
                        "hedefler": ["app"],
                        "deger": ifade_adi(
                            dugum.value
                        ),
                        "kaynak": ast.unparse(
                            dugum
                        ),
                        "kapsam": kapsam_zinciri(
                            dugum,
                            ebeveynler,
                        ),
                    }
                )

        elif isinstance(
            dugum,
            ast.Call,
        ):
            cagri = ifade_adi(
                dugum.func
            )

            if not cagri.endswith(
                "include_router"
            ):
                continue

            include_routerlar.append(
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
                    "kaynak": ast.unparse(
                        dugum
                    ),
                    "kapsam": kapsam_zinciri(
                        dugum,
                        ebeveynler,
                    ),
                }
            )

    return {
        "dosya": yol.as_posix(),
        "sha256": sha256(
            metin.encode(
                "utf-8"
            )
        ).hexdigest(),
        "app_atamalari": app_atamalari,
        "ilgili_importlar": importlar,
        "include_routerlar": (
            include_routerlar
        ),
    }


def yol_listesi(
    nesne: Any,
) -> list[str]:
    return sorted(
        {
            route.path
            for route in getattr(
                nesne,
                "routes",
                (),
            )
            if getattr(
                route,
                "path",
                None,
            )
        }
    )


sunucu_modulu = importlib.import_module(
    "syk_simulasyon.runtime_ui_sunucusu"
)

api_modulu = importlib.import_module(
    "syk_simulasyon.syk_ui_runtime.api_routes"
)

finans_modulu = importlib.import_module(
    "syk_simulasyon.syk_ui_runtime."
    "syfinans_runtime_routes"
)

app = getattr(
    sunucu_modulu,
    "app"
)

syk_ui_router = getattr(
    api_modulu,
    "router"
)

finans_router = getattr(
    finans_modulu,
    "finans_router"
)

runtime = {
    "sunucu_modul_dosyasi": inspect.getfile(
        sunucu_modulu
    ),
    "api_modul_dosyasi": inspect.getfile(
        api_modulu
    ),
    "finans_modul_dosyasi": inspect.getfile(
        finans_modulu
    ),
    "app_id": id(
        app
    ),
    "app_turu": (
        f"{type(app).__module__}."
        f"{type(app).__qualname__}"
    ),
    "app_yol_sayisi": len(
        yol_listesi(
            app
        )
    ),
    "app_yollari": yol_listesi(
        app
    ),
    "syk_ui_router_id": id(
        syk_ui_router
    ),
    "syk_ui_router_yol_sayisi": len(
        yol_listesi(
            syk_ui_router
        )
    ),
    "syk_ui_router_yollari": yol_listesi(
        syk_ui_router
    ),
    "finans_router_id": id(
        finans_router
    ),
    "finans_router_yol_sayisi": len(
        yol_listesi(
            finans_router
        )
    ),
    "finans_router_yollari": yol_listesi(
        finans_router
    ),
}

rapor_temeli = {
    "schema": (
        "syk-router-kapsam-ve-"
        "app-kimlik-incelemesi/v1"
    ),
    "sunucu_kaynagi": kaynak_kayitlari(
        SUNUCU
    ),
    "api_routes_kaynagi": (
        kaynak_kayitlari(
            API_ROUTES
        )
    ),
    "finans_routes_kaynagi": (
        kaynak_kayitlari(
            FINANS_ROUTES
        )
    ),
    "runtime": runtime,
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
    (
        "SYK ROUTER KAPSAM VE APP "
        "KİMLİK İNCELEMESİ"
    ),
    "",
    "GERÇEK YÜKLENEN MODÜL DOSYALARI",
    (
        "Sunucu: "
        f"{runtime['sunucu_modul_dosyasi']}"
    ),
    (
        "API routes: "
        f"{runtime['api_modul_dosyasi']}"
    ),
    (
        "Finans routes: "
        f"{runtime['finans_modul_dosyasi']}"
    ),
    "",
    "RUNTIME NESNELERİ",
    (
        "APP ID: "
        f"{runtime['app_id']}"
    ),
    (
        "APP YOL SAYISI: "
        f"{runtime['app_yol_sayisi']}"
    ),
    (
        "SYK UI ROUTER ID: "
        f"{runtime['syk_ui_router_id']}"
    ),
    (
        "SYK UI ROUTER YOL SAYISI: "
        f"{runtime['syk_ui_router_yol_sayisi']}"
    ),
    (
        "FİNANS ROUTER ID: "
        f"{runtime['finans_router_id']}"
    ),
    (
        "FİNANS ROUTER YOL SAYISI: "
        f"{runtime['finans_router_yol_sayisi']}"
    ),
    "",
    "SUNUCU APP ATAMALARI",
]

for kayit in rapor[
    "sunucu_kaynagi"
][
    "app_atamalari"
]:
    satirlar.append(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
        )
    )

satirlar.extend(
    [
        "",
        "SUNUCU İLGİLİ IMPORTLARI",
    ]
)

for kayit in rapor[
    "sunucu_kaynagi"
][
    "ilgili_importlar"
]:
    satirlar.append(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
        )
    )

satirlar.extend(
    [
        "",
        "SUNUCU INCLUDE_ROUTER KAYITLARI",
    ]
)

for kayit in rapor[
    "sunucu_kaynagi"
][
    "include_routerlar"
]:
    satirlar.append(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
        )
    )

satirlar.extend(
    [
        "",
        "API_ROUTES INCLUDE_ROUTER KAYITLARI",
    ]
)

for kayit in rapor[
    "api_routes_kaynagi"
][
    "include_routerlar"
]:
    satirlar.append(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
        )
    )

satirlar.extend(
    [
        "",
        "APP İLGİLİ YOLLARI",
    ]
)

for yol in runtime[
    "app_yollari"
]:
    if any(
        ifade in yol.casefold()
        for ifade in (
            "syk-ui",
            "mobile",
            "jarmin",
            "kasif",
            "finans",
        )
    ):
        satirlar.append(
            yol
        )

satirlar.extend(
    [
        "",
        "SYK UI ROUTER YOLLARI",
    ]
)

satirlar.extend(
    runtime[
        "syk_ui_router_yollari"
    ]
)

satirlar.extend(
    [
        "",
        "FİNANS ROUTER YOLLARI",
    ]
)

satirlar.extend(
    runtime[
        "finans_router_yollari"
    ]
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
    "SYK_ROUTER_KAPSAM_VE_APP_"
    "KIMLIK_INCELEMESI_OK"
)

print(
    "APP_YOLU",
    runtime["app_yol_sayisi"],
)

print(
    "SYK_UI_ROUTER_YOLU",
    runtime[
        "syk_ui_router_yol_sayisi"
    ],
)

print(
    "FINANS_ROUTER_YOLU",
    runtime[
        "finans_router_yol_sayisi"
    ],
)

print(
    "SUNUCU_INCLUDE_ROUTER",
    len(
        rapor[
            "sunucu_kaynagi"
        ][
            "include_routerlar"
        ]
    ),
)

print(
    "RAPOR",
    RAPOR_TXT,
)