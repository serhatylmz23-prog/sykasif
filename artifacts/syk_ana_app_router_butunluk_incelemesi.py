from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys
from typing import Any


PROJE_KOKU = Path(".")
SRC = Path("src")
TESTS = Path("tests")
ARTIFACTS = Path("artifacts")

RAPOR_JSON = ARTIFACTS / (
    "SYK_ANA_APP_ROUTER_BUTUNLUK_INCELEMESI.json"
)

RAPOR_TXT = ARTIFACTS / (
    "SYK_ANA_APP_ROUTER_BUTUNLUK_INCELEMESI.txt"
)


HEDEF_TESTLER = (
    "test_jarmin_integration_api.py",
    "test_spr_006_mobile_runtime_closure.py",
    "test_ui_kasif_icon_api.py",
    "test_ui_mobile_control_api.py",
    "test_ui_mobile_device_runtime_api.py",
    "test_ui_mobile_offline_runtime_api.py",
    "test_ui_mobile_sensor_runtime_api.py",
)


BEKLENEN_YOLLAR = (
    "/api/syk-ui/jarmin/integration",
    "/api/syk-ui/mobile-runtime",
    "/api/syk-ui/mobile-sensors",
    "/api/syk-ui/mobile-offline",
    "/api/syk-ui/mobile-control",
    "/api/syk-ui/kasif-icons",
    "/syfinans/runtime",
)


@dataclass(frozen=True, slots=True)
class AppIceAktarimi:
    test_dosyasi: str
    modul: str
    nesne: str
    satir: int


@dataclass(frozen=True, slots=True)
class RouterAdayi:
    dosya: str
    nesne: str
    prefix: str | None
    tags: tuple[str, ...]
    satir: int


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
    if isinstance(dugum, ast.Name):
        return dugum.id

    if isinstance(dugum, ast.Attribute):
        onceki = ifade_adi(
            dugum.value
        )

        return (
            f"{onceki}.{dugum.attr}"
            if onceki
            else dugum.attr
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


def test_app_ice_aktarmalari() -> tuple[
    AppIceAktarimi,
    ...
]:
    bulunanlar: list[
        AppIceAktarimi
    ] = []

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

            modul = dugum.module

            if not modul:
                continue

            for ad in dugum.names:
                if ad.name != "app":
                    continue

                bulunanlar.append(
                    AppIceAktarimi(
                        test_dosyasi=(
                            yol.as_posix()
                        ),
                        modul=modul,
                        nesne=(
                            ad.asname
                            or ad.name
                        ),
                        satir=dugum.lineno,
                    )
                )

    return tuple(
        bulunanlar
    )


def router_adaylarini_bul() -> tuple[
    RouterAdayi,
    ...
]:
    adaylar: list[
        RouterAdayi
    ] = []

    for yol in sorted(
        SRC.rglob("*.py")
    ):
        if "__pycache__" in yol.parts:
            continue

        try:
            agac = ast.parse(
                oku(yol),
                filename=str(yol),
            )
        except SyntaxError:
            continue

        for dugum in agac.body:
            if not isinstance(
                dugum,
                ast.Assign,
            ):
                continue

            if not isinstance(
                dugum.value,
                ast.Call,
            ):
                continue

            cagri = ifade_adi(
                dugum.value.func
            )

            if not cagri.endswith(
                "APIRouter"
            ):
                continue

            prefix = None
            tags: tuple[str, ...] = ()

            for anahtar in (
                dugum.value.keywords
            ):
                if anahtar.arg == "prefix":
                    prefix = sabit(
                        anahtar.value
                    )

                if anahtar.arg == "tags":
                    deger = sabit(
                        anahtar.value
                    )

                    if isinstance(
                        deger,
                        (list, tuple),
                    ):
                        tags = tuple(
                            str(oge)
                            for oge in deger
                        )

            for hedef in dugum.targets:
                nesne = ifade_adi(
                    hedef
                )

                if not nesne:
                    continue

                adaylar.append(
                    RouterAdayi(
                        dosya=yol.as_posix(),
                        nesne=nesne,
                        prefix=(
                            str(prefix)
                            if prefix is not None
                            else None
                        ),
                        tags=tags,
                        satir=dugum.lineno,
                    )
                )

    return tuple(
        adaylar
    )


def modulu_dosyaya_cevir(
    modul: str,
) -> Path | None:
    aday = SRC.joinpath(
        *modul.split(".")
    ).with_suffix(".py")

    if aday.is_file():
        return aday

    paket_adayi = SRC.joinpath(
        *modul.split("."),
        "__init__.py",
    )

    if paket_adayi.is_file():
        return paket_adayi

    return None


def app_kaynak_incelemesi(
    modul: str,
) -> dict[str, Any]:
    yol = modulu_dosyaya_cevir(
        modul
    )

    if yol is None:
        return {
            "modul": modul,
            "dosya": None,
            "hata": (
                "Modül kaynak dosyası "
                "bulunamadı."
            ),
        }

    metin = oku(
        yol
    )

    agac = ast.parse(
        metin,
        filename=str(yol),
    )

    app_atamalari = []
    include_router = []
    importlar = []

    for dugum in ast.walk(
        agac
    ):
        if isinstance(
            dugum,
            ast.ImportFrom,
        ):
            importlar.append(
                {
                    "satir": dugum.lineno,
                    "modul": dugum.module,
                    "adlar": [
                        ad.name
                        for ad in dugum.names
                    ],
                }
            )

        elif isinstance(
            dugum,
            ast.Assign,
        ):
            if not isinstance(
                dugum.value,
                ast.Call,
            ):
                continue

            cagri = ifade_adi(
                dugum.value.func
            )

            if not cagri.endswith(
                "FastAPI"
            ):
                continue

            app_atamalari.append(
                {
                    "satir": dugum.lineno,
                    "hedefler": [
                        ifade_adi(hedef)
                        for hedef
                        in dugum.targets
                    ],
                    "cagri": cagri,
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

            include_router.append(
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
                    "prefix": next(
                        (
                            sabit(
                                anahtar.value
                            )
                            for anahtar
                            in dugum.keywords
                            if anahtar.arg
                            == "prefix"
                        ),
                        None,
                    ),
                }
            )

    return {
        "modul": modul,
        "dosya": yol.as_posix(),
        "sha256": sha256(
            metin.encode("utf-8")
        ).hexdigest(),
        "app_atamalari": app_atamalari,
        "include_router": include_router,
        "importlar": importlar,
    }


def runtime_yollarini_getir(
    modul: str,
) -> dict[str, Any]:
    try:
        yuklenen = importlib.import_module(
            modul
        )

        app = getattr(
            yuklenen,
            "app",
        )

        yollar = []

        for route in app.routes:
            path = getattr(
                route,
                "path",
                None,
            )

            if not path:
                continue

            methods = sorted(
                getattr(
                    route,
                    "methods",
                    (),
                )
                or ()
            )

            yollar.append(
                {
                    "path": path,
                    "methods": methods,
                    "name": getattr(
                        route,
                        "name",
                        None,
                    ),
                }
            )

        yollar.sort(
            key=lambda kayit: (
                kayit["path"],
                kayit["methods"],
            )
        )

        return {
            "basarili": True,
            "modul": modul,
            "yollar": yollar,
        }

    except Exception as error:
        return {
            "basarili": False,
            "modul": modul,
            "hata_turu": (
                type(error).__name__
            ),
            "hata": str(error),
            "yollar": [],
        }


app_ice_aktarmalari = (
    test_app_ice_aktarmalari()
)

app_modulleri = tuple(
    sorted(
        {
            kayit.modul
            for kayit
            in app_ice_aktarmalari
        }
    )
)

router_adaylari = (
    router_adaylarini_bul()
)

app_kaynaklari = [
    app_kaynak_incelemesi(
        modul
    )
    for modul in app_modulleri
]

runtime_sonuclari = [
    runtime_yollarini_getir(
        modul
    )
    for modul in app_modulleri
]

tum_runtime_yollari = {
    yol["path"]
    for sonuc in runtime_sonuclari
    for yol in sonuc.get(
        "yollar",
        [],
    )
}

eksik_yollar = [
    beklenen
    for beklenen in BEKLENEN_YOLLAR
    if not any(
        mevcut == beklenen
        or mevcut.startswith(
            beklenen + "/"
        )
        or beklenen.startswith(
            mevcut.rstrip("/") + "/"
        )
        for mevcut
        in tum_runtime_yollari
    )
]

ilgili_router_adaylari = [
    asdict(aday)
    for aday in router_adaylari
    if any(
        ifade in (
            (
                aday.prefix
                or ""
            )
            + " "
            + aday.dosya
            + " "
            + " ".join(
                aday.tags
            )
        ).casefold()
        for ifade in (
            "jarmin",
            "kasif",
            "mobile",
            "sensor",
            "offline",
            "control",
            "finans",
        )
    )
]

rapor_temeli = {
    "schema": (
        "syk-ana-app-router-"
        "butunluk-incelemesi/v1"
    ),
    "python": sys.version,
    "app_ice_aktarmalari": [
        asdict(kayit)
        for kayit
        in app_ice_aktarmalari
    ],
    "app_modulleri": list(
        app_modulleri
    ),
    "app_kaynaklari": (
        app_kaynaklari
    ),
    "runtime_sonuclari": (
        runtime_sonuclari
    ),
    "beklenen_yollar": list(
        BEKLENEN_YOLLAR
    ),
    "eksik_yollar": (
        eksik_yollar
    ),
    "ilgili_router_adaylari": (
        ilgili_router_adaylari
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
    (
        "SYK ANA APP ROUTER "
        "BÜTÜNLÜK İNCELEMESİ"
    ),
    "",
    "APP İÇE AKTARMALARI",
]

for kayit in app_ice_aktarmalari:
    satirlar.append(
        (
            f"{kayit.test_dosyasi}:"
            f"{kayit.satir} | "
            f"from {kayit.modul} "
            f"import app"
        )
    )

satirlar.extend(
    [
        "",
        "APP MODÜLLERİ",
    ]
)

for modul in app_modulleri:
    satirlar.append(
        modul
    )

satirlar.extend(
    [
        "",
        "RUNTIME YOL SAYILARI",
    ]
)

for sonuc in runtime_sonuclari:
    satirlar.append(
        (
            f"{sonuc['modul']} | "
            f"başarılı={sonuc['basarili']} | "
            f"yol={len(sonuc.get('yollar', []))}"
        )
    )

satirlar.extend(
    [
        "",
        "EKSİK BEKLENEN YOLLAR",
    ]
)

if eksik_yollar:
    satirlar.extend(
        eksik_yollar
    )
else:
    satirlar.append(
        "Eksik yol bulunmadı."
    )

satirlar.extend(
    [
        "",
        "İLGİLİ ROUTER ADAYLARI",
    ]
)

for aday in ilgili_router_adaylari:
    satirlar.append(
        (
            f"{aday['dosya']}:{aday['satir']} | "
            f"{aday['nesne']} | "
            f"prefix={aday['prefix']} | "
            f"tags={aday['tags']}"
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
    "SYK_ANA_APP_ROUTER_"
    "BUTUNLUK_INCELEMESI_OK"
)

print(
    "APP_MODULU_SAYISI",
    len(app_modulleri),
)

print(
    "ROUTER_ADAYI_SAYISI",
    len(ilgili_router_adaylari),
)

print(
    "EKSIK_YOL_SAYISI",
    len(eksik_yollar),
)

for yol in eksik_yollar:
    print(
        "EKSIK_YOL",
        yol,
    )

print(
    "RAPOR",
    RAPOR_TXT,
)
