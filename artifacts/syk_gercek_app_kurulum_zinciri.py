from __future__ import annotations

import ast
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any


SRC = Path("src")
TESTS = Path("tests")

SUNUCU = Path(
    "src/syk_simulasyon/"
    "runtime_ui_sunucusu.py"
)

API_ROUTES = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/api_routes.py"
)

RAPOR_JSON = Path(
    "artifacts/"
    "SYK_GERCEK_APP_KURULUM_ZINCIRI.json"
)

RAPOR_TXT = Path(
    "artifacts/"
    "SYK_GERCEK_APP_KURULUM_ZINCIRI.txt"
)

HEDEF_TESTLER = (
    "test_jarmin_integration_api.py",
    "test_spr_006_mobile_runtime_closure.py",
    "test_ui_kasif_icon_api.py",
    "test_ui_mobile_control_api.py",
    "test_ui_mobile_device_runtime_api.py",
    "test_ui_mobile_offline_runtime_api.py",
    "test_ui_mobile_sensor_runtime_api.py",
    "test_syfinans_runtime_routes.py",
)


def oku(
    yol: Path,
) -> str:
    return yol.read_text(
        encoding="utf-8",
        errors="replace",
    )


def ifade_adi(
    dugum: ast.AST,
) -> str:
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


def sabit(
    dugum: ast.AST,
) -> Any:
    try:
        return ast.literal_eval(
            dugum
        )
    except Exception:
        return None


def kaynak_incele(
    yol: Path,
) -> dict[str, Any]:
    metin = oku(
        yol
    )

    agac = ast.parse(
        metin,
        filename=str(yol),
    )

    app_atamalari = []
    router_atamalari = []
    cagri_kayitlari = []
    fonksiyonlar = []
    donusler = []

    for dugum in ast.walk(
        agac
    ):
        if isinstance(
            dugum,
            ast.Assign,
        ):
            hedefler = [
                ifade_adi(
                    hedef
                )
                for hedef in dugum.targets
            ]

            cagri = (
                ifade_adi(
                    dugum.value.func
                )
                if isinstance(
                    dugum.value,
                    ast.Call,
                )
                else ""
            )

            kayit = {
                "satir": dugum.lineno,
                "hedefler": hedefler,
                "cagri": cagri,
            }

            if "app" in hedefler:
                app_atamalari.append(
                    kayit
                )

            if "router" in hedefler:
                router_atamalari.append(
                    kayit
                )

        elif isinstance(
            dugum,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            fonksiyonlar.append(
                {
                    "ad": dugum.name,
                    "satir": dugum.lineno,
                    "parametreler": [
                        arg.arg
                        for arg
                        in dugum.args.args
                    ],
                }
            )

        elif isinstance(
            dugum,
            ast.Call,
        ):
            cagri = ifade_adi(
                dugum.func
            )

            if (
                cagri.endswith(
                    "include_router"
                )
                or cagri.endswith(
                    "mount"
                )
                or cagri.endswith(
                    "add_api_route"
                )
            ):
                cagri_kayitlari.append(
                    {
                        "satir": getattr(
                            dugum,
                            "lineno",
                            0,
                        ),
                        "cagri": cagri,
                        "argumanlar": [
                            ifade_adi(
                                arguman
                            )
                            or sabit(
                                arguman
                            )
                            for arguman
                            in dugum.args
                        ],
                        "anahtarlar": {
                            anahtar.arg: (
                                ifade_adi(
                                    anahtar.value
                                )
                                or sabit(
                                    anahtar.value
                                )
                            )
                            for anahtar
                            in dugum.keywords
                            if anahtar.arg
                        },
                    }
                )

        elif isinstance(
            dugum,
            ast.Return,
        ):
            donusler.append(
                {
                    "satir": dugum.lineno,
                    "deger": ifade_adi(
                        dugum.value
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
        "router_atamalari": (
            router_atamalari
        ),
        "cagri_kayitlari": (
            cagri_kayitlari
        ),
        "fonksiyonlar": fonksiyonlar,
        "donusler": donusler,
    }


def test_app_importlari(
) -> list[dict[str, Any]]:
    sonuclar = []

    for dosya_adi in HEDEF_TESTLER:
        yol = TESTS / dosya_adi

        if not yol.is_file():
            continue

        agac = ast.parse(
            oku(yol),
            filename=str(yol),
        )

        for dugum in agac.body:
            if not isinstance(
                dugum,
                ast.ImportFrom,
            ):
                continue

            for ad in dugum.names:
                if ad.name != "app":
                    continue

                sonuclar.append(
                    {
                        "test": yol.as_posix(),
                        "satir": dugum.lineno,
                        "modul": dugum.module,
                        "yerel_ad": (
                            ad.asname
                            or ad.name
                        ),
                    }
                )

    return sonuclar


def runtime_modul_incele(
    modul_adi: str,
) -> dict[str, Any]:
    try:
        modul = importlib.import_module(
            modul_adi
        )

        app = getattr(
            modul,
            "app",
            None,
        )

        if app is None:
            return {
                "modul": modul_adi,
                "basarili": False,
                "hata": (
                    "Modülde app nesnesi yok."
                ),
            }

        yollar = sorted(
            {
                route.path
                for route in app.routes
                if getattr(
                    route,
                    "path",
                    None,
                )
            }
        )

        return {
            "modul": modul_adi,
            "basarili": True,
            "app_turu": (
                f"{type(app).__module__}."
                f"{type(app).__qualname__}"
            ),
            "app_id": id(app),
            "yol_sayisi": len(
                yollar
            ),
            "yollar": yollar,
        }

    except Exception as error:
        return {
            "modul": modul_adi,
            "basarili": False,
            "hata_turu": (
                type(error).__name__
            ),
            "hata": str(error),
        }


sunucu_incelemesi = kaynak_incele(
    SUNUCU
)

api_incelemesi = kaynak_incele(
    API_ROUTES
)

test_importlari = (
    test_app_importlari()
)

app_modulleri = sorted(
    {
        kayit["modul"]
        for kayit
        in test_importlari
        if kayit.get(
            "modul"
        )
    }
)

runtime_modulleri = [
    runtime_modul_incele(
        modul
    )
    for modul in app_modulleri
]

rapor_temeli = {
    "schema": (
        "syk-gercek-app-kurulum-zinciri/v1"
    ),
    "sunucu_incelemesi": (
        sunucu_incelemesi
    ),
    "api_routes_incelemesi": (
        api_incelemesi
    ),
    "test_app_importlari": (
        test_importlari
    ),
    "app_modulleri": (
        app_modulleri
    ),
    "runtime_modulleri": (
        runtime_modulleri
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

satirlar = [
    "SYK GERÇEK APP KURULUM ZİNCİRİ",
    "",
    "TESTLERİN KULLANDIĞI APP MODÜLLERİ",
]

for kayit in test_importlari:
    satirlar.append(
        (
            f"{kayit['test']}:"
            f"{kayit['satir']} | "
            f"from {kayit['modul']} "
            "import app"
        )
    )

satirlar.extend(
    [
        "",
        "RUNTIME APP NESNELERİ",
    ]
)

for kayit in runtime_modulleri:
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
        "RUNTIME_UI_SUNUCUSU APP ATAMALARI",
    ]
)

for kayit in sunucu_incelemesi[
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
        "RUNTIME_UI_SUNUCUSU ROUTER/MOUNT ÇAĞRILARI",
    ]
)

for kayit in sunucu_incelemesi[
    "cagri_kayitlari"
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
        "API_ROUTES ROUTER ATAMALARI",
    ]
)

for kayit in api_incelemesi[
    "router_atamalari"
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
        "API_ROUTES INCLUDE ROUTER ÇAĞRILARI",
    ]
)

for kayit in api_incelemesi[
    "cagri_kayitlari"
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
    "SYK_GERCEK_APP_KURULUM_ZINCIRI_OK"
)

print(
    "APP_MODULU_SAYISI",
    len(
        app_modulleri
    ),
)

for kayit in runtime_modulleri:
    print(
        "APP_MODULU",
        kayit.get(
            "modul"
        ),
        "BASARILI",
        kayit.get(
            "basarili"
        ),
        "YOL_SAYISI",
        kayit.get(
            "yol_sayisi",
            0,
        ),
        "APP_ID",
        kayit.get(
            "app_id",
            "-",
        ),
    )

print(
    "SUNUCU_APP_ATAMASI",
    len(
        sunucu_incelemesi[
            "app_atamalari"
        ]
    ),
)

print(
    "SUNUCU_ROUTER_MOUNT",
    len(
        sunucu_incelemesi[
            "cagri_kayitlari"
        ]
    ),
)

print(
    "API_ROUTER_ATAMASI",
    len(
        api_incelemesi[
            "router_atamalari"
        ]
    ),
)

print(
    "API_INCLUDE_ROUTER",
    len(
        api_incelemesi[
            "cagri_kayitlari"
        ]
    ),
)

print(
    "RAPOR",
    RAPOR_TXT,
)