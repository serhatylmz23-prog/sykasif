from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


HEDEF = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/api_routes.py"
)

RAPOR_JSON = Path(
    "artifacts/"
    "SYFINANS_RUNTIME_API_ROUTES_INCELEME.json"
)

RAPOR_TXT = Path(
    "artifacts/"
    "SYFINANS_RUNTIME_API_ROUTES_INCELEME.txt"
)


if not HEDEF.is_file():
    raise FileNotFoundError(
        HEDEF
    )


metin = HEDEF.read_text(
    encoding="utf-8"
)

agac = ast.parse(
    metin,
    filename=str(
        HEDEF
    ),
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


def sabit_deger(
    dugum: ast.AST,
) -> Any:
    try:
        return ast.literal_eval(
            dugum
        )
    except Exception:
        return None


ice_aktarmalar: list[
    dict[str, Any]
] = []

atamalar: list[
    dict[str, Any]
] = []

fonksiyonlar: list[
    dict[str, Any]
] = []

siniflar: list[
    dict[str, Any]
] = []

yollar: list[
    dict[str, Any]
] = []

router_nesneleri: list[
    dict[str, Any]
] = []

uygulama_nesneleri: list[
    dict[str, Any]
] = []

include_router_cagrilari: list[
    dict[str, Any]
] = []

mount_cagrilari: list[
    dict[str, Any]
] = []


for dugum in ast.walk(
    agac
):
    if isinstance(
        dugum,
        ast.Import,
    ):
        ice_aktarmalar.append(
            {
                "tur": "import",
                "satir": dugum.lineno,
                "moduller": [
                    ad.name
                    for ad in dugum.names
                ],
            }
        )

    elif isinstance(
        dugum,
        ast.ImportFrom,
    ):
        ice_aktarmalar.append(
            {
                "tur": "from",
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
        hedefler = [
            ifade_adi(
                hedef
            )
            for hedef in dugum.targets
        ]

        cagri_adi = (
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
            "cagri": cagri_adi,
            "deger": sabit_deger(
                dugum.value
            ),
        }

        atamalar.append(
            kayit
        )

        if cagri_adi.endswith(
            "APIRouter"
        ):
            router_nesneleri.append(
                kayit
            )

        if cagri_adi.endswith(
            "FastAPI"
        ):
            uygulama_nesneleri.append(
                kayit
            )

    elif isinstance(
        dugum,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ):
        dekoratorler = [
            ifade_adi(
                dekorator.func
            )
            if isinstance(
                dekorator,
                ast.Call,
            )
            else ifade_adi(
                dekorator
            )
            for dekorator
            in dugum.decorator_list
        ]

        fonksiyonlar.append(
            {
                "ad": dugum.name,
                "satir": dugum.lineno,
                "asenkron": isinstance(
                    dugum,
                    ast.AsyncFunctionDef,
                ),
                "dekoratorler": dekoratorler,
                "parametreler": [
                    arg.arg
                    for arg
                    in dugum.args.args
                ],
            }
        )

        for dekorator in dugum.decorator_list:
            if not isinstance(
                dekorator,
                ast.Call,
            ):
                continue

            dekorator_adi = ifade_adi(
                dekorator.func
            )

            yontem = dekorator_adi.rsplit(
                ".",
                1,
            )[-1].casefold()

            if yontem not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
                "route",
                "websocket",
            }:
                continue

            yol = (
                sabit_deger(
                    dekorator.args[0]
                )
                if dekorator.args
                else None
            )

            yollar.append(
                {
                    "fonksiyon": dugum.name,
                    "satir": dugum.lineno,
                    "dekorator": dekorator_adi,
                    "yontem": yontem,
                    "yol": yol,
                    "anahtarlar": {
                        anahtar.arg: sabit_deger(
                            anahtar.value
                        )
                        for anahtar
                        in dekorator.keywords
                        if anahtar.arg
                    },
                }
            )

    elif isinstance(
        dugum,
        ast.ClassDef,
    ):
        siniflar.append(
            {
                "ad": dugum.name,
                "satir": dugum.lineno,
                "tabanlar": [
                    ifade_adi(
                        taban
                    )
                    for taban in dugum.bases
                ],
            }
        )

    elif isinstance(
        dugum,
        ast.Call,
    ):
        cagri_adi = ifade_adi(
            dugum.func
        )

        kayit = {
            "satir": getattr(
                dugum,
                "lineno",
                0,
            ),
            "cagri": cagri_adi,
            "argumanlar": [
                sabit_deger(
                    arguman
                )
                for arguman in dugum.args
            ],
            "anahtarlar": {
                anahtar.arg: sabit_deger(
                    anahtar.value
                )
                for anahtar
                in dugum.keywords
                if anahtar.arg
            },
        }

        if cagri_adi.endswith(
            "include_router"
        ):
            include_router_cagrilari.append(
                kayit
            )

        if cagri_adi.endswith(
            "mount"
        ):
            mount_cagrilari.append(
                kayit
            )


ilgili_ifadeler = (
    "FastAPI",
    "APIRouter",
    "include_router",
    "StaticFiles",
    "HTMLResponse",
    "JSONResponse",
    "FileResponse",
    "Depends",
    "Request",
    "Response",
    "syk-ui-screen",
    "mobile",
    "runtime",
    "router",
    "app",
)

ilgili_satirlar: list[
    dict[str, Any]
] = []

for sira, satir in enumerate(
    metin.splitlines(),
    start=1,
):
    if any(
        ifade.casefold()
        in satir.casefold()
        for ifade in ilgili_ifadeler
    ):
        ilgili_satirlar.append(
            {
                "satir": sira,
                "metin": satir.rstrip(),
            }
        )


ust_dizin = HEDEF.parent

kardes_dosyalar = sorted(
    yol.as_posix()
    for yol in ust_dizin.glob(
        "*.py"
    )
    if yol.is_file()
)

init_yolu = (
    ust_dizin
    / "__init__.py"
)

init_icerigi = (
    init_yolu.read_text(
        encoding="utf-8"
    )
    if init_yolu.is_file()
    else None
)


rapor = {
    "schema": (
        "syfinans-runtime-api-routes-"
        "inceleme/v1"
    ),
    "hedef": HEDEF.as_posix(),
    "hedef_sha256": sha256(
        metin.encode(
            "utf-8"
        )
    ).hexdigest(),
    "satir_sayisi": len(
        metin.splitlines()
    ),
    "ice_aktarmalar": (
        ice_aktarmalar
    ),
    "atamalar": atamalar,
    "router_nesneleri": (
        router_nesneleri
    ),
    "uygulama_nesneleri": (
        uygulama_nesneleri
    ),
    "fonksiyonlar": (
        fonksiyonlar
    ),
    "siniflar": siniflar,
    "http_yollari": yollar,
    "include_router_cagrilari": (
        include_router_cagrilari
    ),
    "mount_cagrilari": (
        mount_cagrilari
    ),
    "ilgili_satirlar": (
        ilgili_satirlar
    ),
    "kardes_dosyalar": (
        kardes_dosyalar
    ),
    "init_var": (
        init_yolu.is_file()
    ),
    "init_icerigi": (
        init_icerigi
    ),
}

kodlu = json.dumps(
    rapor,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")

rapor[
    "rapor_sha256"
] = sha256(
    kodlu
).hexdigest()


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
        "SYFİNANS RUNTIME API_ROUTES "
        "MİMARİ İNCELEMESİ"
    ),
    "",
    f"HEDEF: {HEDEF.as_posix()}",
    (
        "HEDEF SHA-256: "
        f"{rapor['hedef_sha256']}"
    ),
    (
        "SATIR SAYISI: "
        f"{rapor['satir_sayisi']}"
    ),
    (
        "ROUTER NESNESİ: "
        f"{len(router_nesneleri)}"
    ),
    (
        "FASTAPI NESNESİ: "
        f"{len(uygulama_nesneleri)}"
    ),
    (
        "HTTP YOLU: "
        f"{len(yollar)}"
    ),
    (
        "FONKSİYON: "
        f"{len(fonksiyonlar)}"
    ),
    (
        "SINIF: "
        f"{len(siniflar)}"
    ),
    "",
    "ROUTER NESNELERİ",
]

if router_nesneleri:
    for kayit in router_nesneleri:
        satirlar.append(
            (
                f"Satır {kayit['satir']} | "
                f"{kayit['hedefler']} | "
                f"{kayit['cagri']}"
            )
        )
else:
    satirlar.append(
        "Bulunamadı."
    )


satirlar.extend(
    [
        "",
        "FASTAPI NESNELERİ",
    ]
)

if uygulama_nesneleri:
    for kayit in uygulama_nesneleri:
        satirlar.append(
            (
                f"Satır {kayit['satir']} | "
                f"{kayit['hedefler']} | "
                f"{kayit['cagri']}"
            )
        )
else:
    satirlar.append(
        "Bulunamadı."
    )


satirlar.extend(
    [
        "",
        "HTTP YOLLARI",
    ]
)

if yollar:
    for kayit in yollar:
        satirlar.append(
            (
                f"Satır {kayit['satir']} | "
                f"{kayit['yontem'].upper()} | "
                f"{kayit['yol']} | "
                f"{kayit['fonksiyon']}"
            )
        )
else:
    satirlar.append(
        "Bulunamadı."
    )


satirlar.extend(
    [
        "",
        "FONKSİYONLAR",
    ]
)

for kayit in fonksiyonlar:
    satirlar.append(
        (
            f"Satır {kayit['satir']} | "
            f"{kayit['ad']} | "
            f"dekoratör={kayit['dekoratorler']}"
        )
    )


satirlar.extend(
    [
        "",
        "KARDEŞ RUNTIME DOSYALARI",
    ]
)

for yol in kardes_dosyalar:
    satirlar.append(
        yol
    )


satirlar.extend(
    [
        "",
        "İLGİLİ KAYNAK SATIRLARI",
    ]
)

for kayit in ilgili_satirlar[
    :160
]:
    satirlar.append(
        (
            f"{kayit['satir']:>4} | "
            f"{kayit['metin']}"
        )
    )


satirlar.extend(
    [
        "",
        (
            "RAPOR SHA-256: "
            f"{rapor['rapor_sha256']}"
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
    "SYFINANS_RUNTIME_API_ROUTES_"
    "INCELEME_OK"
)

print(
    "HEDEF",
    HEDEF,
)

print(
    "ROUTER_NESNESI",
    len(
        router_nesneleri
    ),
)

print(
    "FASTAPI_NESNESI",
    len(
        uygulama_nesneleri
    ),
)

print(
    "HTTP_YOLU",
    len(
        yollar
    ),
)

print(
    "KARDES_DOSYA",
    len(
        kardes_dosyalar
    ),
)

print(
    "RAPOR",
    RAPOR_TXT,
)
