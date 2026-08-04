from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import json
import re


KOK = Path(".")
SRC = Path("src")
TESTS = Path("tests")
ARTIFACTS = Path("artifacts")

JSON_RAPOR = ARTIFACTS / (
    "SYFINANS_PROTOTIP_KAPANIS_"
    "MIMARI_INCELEME.json"
)

TXT_RAPOR = ARTIFACTS / (
    "SYFINANS_PROTOTIP_KAPANIS_"
    "MIMARI_INCELEME.txt"
)


def oku(
    yol: Path,
) -> str:
    try:
        return yol.read_text(
            encoding="utf-8",
        )
    except UnicodeDecodeError:
        return yol.read_text(
            encoding="utf-8",
            errors="replace",
        )


def dosyalari_bul(
    kok: Path,
    uzantilar: set[str],
) -> list[Path]:
    if not kok.exists():
        return []

    return sorted(
        yol
        for yol in kok.rglob("*")
        if (
            yol.is_file()
            and yol.suffix.casefold()
            in uzantilar
            and "__pycache__"
            not in yol.parts
        )
    )


python_dosyalari = (
    dosyalari_bul(
        SRC,
        {".py"},
    )
    + dosyalari_bul(
        TESTS,
        {".py"},
    )
)

arayuz_dosyalari = dosyalari_bul(
    SRC,
    {
        ".html",
        ".js",
        ".css",
    },
)


arama_gruplari = {
    "http_yollari": (
        r"@(?:app|router)\."
        r"(?:get|post|put|patch|delete)"
        r"\(\s*[\"']([^\"']+)",
        r"add_api_route\(\s*[\"']"
        r"([^\"']+)",
        r"Route\(\s*[\"']"
        r"([^\"']+)",
    ),
    "syk_ui_yollari": (
        r"[\"']([^\"']*"
        r"(?:syk-ui|syk_ui)"
        r"[^\"']*)[\"']",
    ),
    "terminal_kayitlari": (
        r"(?:module|modul|sekme|tab)"
        r"[^=\n]{0,60}"
        r"[=:]\s*[\"']([^\"']+)",
    ),
    "statik_yollar": (
        r"[\"']([^\"']*"
        r"(?:static|assets|js|css)"
        r"[^\"']*)[\"']",
    ),
    "finans_referanslari": (
        r"[\"']([^\"']*"
        r"(?:syfinans|finans)"
        r"[^\"']*)[\"']",
    ),
}


bulgular: dict[str, list[dict[str, object]]] = {
    anahtar: []
    for anahtar in arama_gruplari
}


for yol in (
    python_dosyalari
    + arayuz_dosyalari
):
    metin = oku(
        yol
    )

    for grup, desenler in (
        arama_gruplari.items()
    ):
        for desen in desenler:
            for eslesme in re.finditer(
                desen,
                metin,
                flags=re.IGNORECASE,
            ):
                satir = (
                    metin.count(
                        "\n",
                        0,
                        eslesme.start(),
                    )
                    + 1
                )

                deger = (
                    eslesme.group(1)
                    if eslesme.groups()
                    else eslesme.group(0)
                )

                kayit = {
                    "dosya": (
                        yol.as_posix()
                    ),
                    "satir": satir,
                    "deger": str(
                        deger
                    ).strip(),
                }

                if kayit not in (
                    bulgular[grup]
                ):
                    bulgular[
                        grup
                    ].append(
                        kayit
                    )


tarayici_testleri: list[
    dict[str, object]
] = []

for yol in python_dosyalari:
    if "test" not in yol.name.casefold():
        continue

    metin = oku(
        yol
    )

    isaretler = []

    for ifade in (
        "page.goto",
        "set_viewport_size",
        "playwright",
        "browser",
        "chromium",
        "expect(",
        "SYK_UI_TEST_URL",
    ):
        if ifade in metin:
            isaretler.append(
                ifade
            )

    if isaretler:
        tarayici_testleri.append(
            {
                "dosya": (
                    yol.as_posix()
                ),
                "isaretler": (
                    isaretler
                ),
            }
        )


runtime_adaylari = []

for yol in python_dosyalari:
    metin = oku(
        yol
    )

    puan = 0
    bulunanlar = []

    for ifade, agirlik in (
        ("FastAPI", 5),
        ("APIRouter", 5),
        ("StaticFiles", 4),
        ("syk-ui-screen", 4),
        ("module_registry", 3),
        ("static_routes", 3),
        ("include_router", 3),
        ("mount(", 2),
        ("uvicorn", 2),
    ):
        if ifade in metin:
            puan += agirlik
            bulunanlar.append(
                ifade
            )

    if puan:
        runtime_adaylari.append(
            {
                "dosya": (
                    yol.as_posix()
                ),
                "puan": puan,
                "isaretler": bulunanlar,
            }
        )

runtime_adaylari.sort(
    key=lambda kayit: (
        -int(
            kayit["puan"]
        ),
        str(
            kayit["dosya"]
        ),
    )
)


finans_dosyalari = sorted(
    yol.as_posix()
    for yol in Path(
        "src/syk_finans_otagi"
    ).glob("*.py")
    if yol.is_file()
)

finans_testleri = sorted(
    yol.as_posix()
    for yol in TESTS.glob(
        "test_syfinans_*.py"
    )
)


ozet = {
    "inceleme_zamani": (
        datetime.now(
            UTC
        ).isoformat()
    ),
    "python_dosyasi_sayisi": len(
        python_dosyalari
    ),
    "arayuz_dosyasi_sayisi": len(
        arayuz_dosyalari
    ),
    "finans_kaynak_dosyasi_sayisi": len(
        finans_dosyalari
    ),
    "finans_test_dosyasi_sayisi": len(
        finans_testleri
    ),
    "runtime_adayi_sayisi": len(
        runtime_adaylari
    ),
    "tarayici_testi_sayisi": len(
        tarayici_testleri
    ),
    "http_yolu_sayisi": len(
        bulgular[
            "http_yollari"
        ]
    ),
}


rapor = {
    "schema": (
        "syfinans-prototip-kapanis-"
        "mimari-inceleme/v1"
    ),
    "ozet": ozet,
    "runtime_adaylari": (
        runtime_adaylari[:30]
    ),
    "tarayici_testleri": (
        tarayici_testleri
    ),
    "bulgular": bulgular,
    "finans_kaynak_dosyalari": (
        finans_dosyalari
    ),
    "finans_test_dosyalari": (
        finans_testleri
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

JSON_RAPOR.write_text(
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
        "SYFİNANS PROTOTİP KAPANIŞ "
        "MİMARİ İNCELEMESİ"
    ),
    "",
    (
        "Python dosyası: "
        f"{ozet['python_dosyasi_sayisi']}"
    ),
    (
        "Arayüz dosyası: "
        f"{ozet['arayuz_dosyasi_sayisi']}"
    ),
    (
        "Finans kaynak dosyası: "
        f"{ozet['finans_kaynak_dosyasi_sayisi']}"
    ),
    (
        "Finans test dosyası: "
        f"{ozet['finans_test_dosyasi_sayisi']}"
    ),
    (
        "Runtime adayı: "
        f"{ozet['runtime_adayi_sayisi']}"
    ),
    (
        "Tarayıcı testi: "
        f"{ozet['tarayici_testi_sayisi']}"
    ),
    (
        "HTTP yolu: "
        f"{ozet['http_yolu_sayisi']}"
    ),
    "",
    "EN GÜÇLÜ RUNTIME ADAYLARI",
]

for kayit in runtime_adaylari[
    :15
]:
    satirlar.append(
        (
            f"{kayit['puan']:>2} | "
            f"{kayit['dosya']} | "
            + ", ".join(
                kayit[
                    "isaretler"
                ]
            )
        )
    )

satirlar.extend(
    [
        "",
        "TARAYICI TESTLERİ",
    ]
)

for kayit in tarayici_testleri:
    satirlar.append(
        (
            f"{kayit['dosya']} | "
            + ", ".join(
                kayit[
                    "isaretler"
                ]
            )
        )
    )

satirlar.extend(
    [
        "",
        "HTTP YOLLARI",
    ]
)

for kayit in bulgular[
    "http_yollari"
][
    :80
]:
    satirlar.append(
        (
            f"{kayit['dosya']}:"
            f"{kayit['satir']} | "
            f"{kayit['deger']}"
        )
    )

satirlar.extend(
    [
        "",
        "MEVCUT FİNANS REFERANSLARI",
    ]
)

for kayit in bulgular[
    "finans_referanslari"
][
    :80
]:
    satirlar.append(
        (
            f"{kayit['dosya']}:"
            f"{kayit['satir']} | "
            f"{kayit['deger']}"
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

TXT_RAPOR.write_text(
    "\n".join(
        satirlar
    )
    + "\n",
    encoding="utf-8",
)

print(
    "SYFINANS_PROTOTIP_KAPANIS_"
    "MIMARI_INCELEME_OK"
)

print(
    "RUNTIME_ADAYI",
    len(
        runtime_adaylari
    ),
)

print(
    "TARAYICI_TESTI",
    len(
        tarayici_testleri
    ),
)

print(
    "HTTP_YOLU",
    len(
        bulgular[
            "http_yollari"
        ]
    ),
)

print(
    "RAPOR",
    TXT_RAPOR,
)
