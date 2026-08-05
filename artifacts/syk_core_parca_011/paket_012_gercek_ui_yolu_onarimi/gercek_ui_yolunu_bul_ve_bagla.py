from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)


KAYNAK = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

SONUC_JSON = Path(
    "artifacts/syk_core_parca_011/"
    "paket_012_gercek_ui_yolu_onarimi/"
    "ui_yol_tarama_sonucu.json"
)

SONUC_TXT = Path(
    "artifacts/syk_core_parca_011/"
    "paket_012_gercek_ui_yolu_onarimi/"
    "ui_yol_tarama_sonucu.txt"
)

ISARET = (
    "# SYK_UI_SCREEN_UYUMLULUK_YOLU"
)

BILIMSEL_ETIKETLER = (
    "Jeoloji",
    "Astronomi",
    "Arkeoastronomi",
    "Kimyasal Analiz",
    "Spektral Analiz",
    "Termal Analiz",
    "Manyetometre",
    "Gravimetre",
    "Elektrik Direnç",
    "GPR",
    "Sismik",
    "Hidrojeoloji",
    "Botanik",
    "Toprak Analizi",
    "Su Analizi",
)

HARIC_YOLLAR = {
    "/syk-ui-screen",
    "/runtime/html",
    "/docs",
    "/redoc",
    "/openapi.json",
}

HTML_IPUCLARI = (
    "<!doctype html",
    "<html",
    "<body",
)

BUTON_IPUCLARI = (
    "<button",
    'role="button"',
    "data-module",
    "module-card",
    "scientific",
    "bilimsel",
)


def sabit_get_yollari(
    uygulama: Any,
) -> list[str]:
    yollar: set[str] = set()

    for route in uygulama.router.routes:
        yol = getattr(
            route,
            "path",
            None,
        )

        metotlar = set(
            getattr(
                route,
                "methods",
                set(),
            )
            or set()
        )

        if not isinstance(
            yol,
            str,
        ):
            continue

        if "GET" not in metotlar:
            continue

        if "{" in yol or "}" in yol:
            continue

        if yol in HARIC_YOLLAR:
            continue

        yollar.add(
            yol
        )

    return sorted(
        yollar
    )


def yaniti_incele(
    istemci: TestClient,
    yol: str,
) -> dict[str, Any]:
    kayit: dict[str, Any] = {
        "yol": yol,
        "durum": None,
        "content_type": "",
        "html_mi": False,
        "uzunluk": 0,
        "etiket_sayisi": 0,
        "etiketler": [],
        "buton_ipucu_sayisi": 0,
        "puan": 0,
        "son_yol": "",
        "hata": None,
    }

    try:
        yanit = istemci.get(
            yol,
            follow_redirects=True,
        )
    except Exception as hata:
        kayit["hata"] = (
            f"{type(hata).__name__}: {hata}"
        )

        return kayit

    icerik_turu = yanit.headers.get(
        "content-type",
        "",
    ).lower()

    metin = yanit.text

    kucuk = metin.casefold()

    html_mi = (
        "text/html" in icerik_turu
        or any(
            ipucu in kucuk
            for ipucu in HTML_IPUCLARI
        )
    )

    bulunan_etiketler = [
        etiket
        for etiket in BILIMSEL_ETIKETLER
        if etiket.casefold() in kucuk
    ]

    buton_ipucu_sayisi = sum(
        kucuk.count(
            ipucu
        )
        for ipucu in BUTON_IPUCLARI
    )

    gercek_button_sayisi = len(
        re.findall(
            r"<button\b",
            metin,
            flags=re.IGNORECASE,
        )
    )

    aria_button_sayisi = len(
        re.findall(
            r"""role\s*=\s*["']button["']""",
            metin,
            flags=re.IGNORECASE,
        )
    )

    puan = 0

    if yanit.status_code == 200:
        puan += 10

    if html_mi:
        puan += 20

    puan += (
        len(
            bulunan_etiketler
        )
        * 20
    )

    puan += min(
        gercek_button_sayisi * 3,
        60,
    )

    puan += min(
        aria_button_sayisi * 2,
        30,
    )

    puan += min(
        buton_ipucu_sayisi,
        30,
    )

    kayit.update(
        {
            "durum": yanit.status_code,
            "content_type": icerik_turu,
            "html_mi": html_mi,
            "uzunluk": len(metin),
            "etiket_sayisi": len(
                bulunan_etiketler
            ),
            "etiketler": bulunan_etiketler,
            "button_sayisi": (
                gercek_button_sayisi
            ),
            "aria_button_sayisi": (
                aria_button_sayisi
            ),
            "buton_ipucu_sayisi": (
                buton_ipucu_sayisi
            ),
            "puan": puan,
            "son_yol": str(
                yanit.url
            ),
            "ilk_500": metin[:500],
        }
    )

    return kayit


def gercek_ui_yolunu_bul() -> tuple[
    str,
    list[dict[str, Any]],
]:
    uygulama = uygulama_olustur()

    yollar = sabit_get_yollari(
        uygulama
    )

    if not yollar:
        raise RuntimeError(
            "Taranabilecek sabit GET yolu bulunamadı."
        )

    with TestClient(
        uygulama,
    ) as istemci:
        kayitlar = [
            yaniti_incele(
                istemci,
                yol,
            )
            for yol in yollar
        ]

    sirali = sorted(
        kayitlar,
        key=lambda kayit: (
            int(
                kayit.get(
                    "puan",
                    0,
                )
            ),
            int(
                kayit.get(
                    "etiket_sayisi",
                    0,
                )
            ),
            int(
                kayit.get(
                    "button_sayisi",
                    0,
                )
            ),
            int(
                kayit.get(
                    "uzunluk",
                    0,
                )
            ),
        ),
        reverse=True,
    )

    uygunlar = [
        kayit
        for kayit in sirali
        if (
            kayit.get(
                "durum"
            )
            == 200
            and kayit.get(
                "html_mi"
            )
            and int(
                kayit.get(
                    "etiket_sayisi",
                    0,
                )
            )
            >= 3
            and (
                int(
                    kayit.get(
                        "button_sayisi",
                        0,
                    )
                )
                > 0
                or int(
                    kayit.get(
                        "aria_button_sayisi",
                        0,
                    )
                )
                > 0
            )
        )
    ]

    if not uygunlar:
        ilk_on = [
            {
                "yol": kayit.get(
                    "yol"
                ),
                "durum": kayit.get(
                    "durum"
                ),
                "html_mi": kayit.get(
                    "html_mi"
                ),
                "etiket_sayisi": (
                    kayit.get(
                        "etiket_sayisi"
                    )
                ),
                "button_sayisi": (
                    kayit.get(
                        "button_sayisi"
                    )
                ),
                "aria_button_sayisi": (
                    kayit.get(
                        "aria_button_sayisi"
                    )
                ),
                "puan": kayit.get(
                    "puan"
                ),
            }
            for kayit in sirali[:10]
        ]

        raise RuntimeError(
            "Bilimsel modülleri ve düğmeleri içeren "
            "gerçek UI yolu bulunamadı. "
            "EN_YUKSEK_ADAYLAR="
            + json.dumps(
                ilk_on,
                ensure_ascii=False,
            )
        )

    secilen = uygunlar[0]

    return (
        str(
            secilen[
                "yol"
            ]
        ),
        sirali,
    )


def uyumluluk_hedefini_guncelle(
    yeni_hedef: str,
) -> tuple[
    bool,
    str | None,
]:
    kaynak = KAYNAK.read_text(
        encoding="utf-8-sig"
    )

    if ISARET not in kaynak:
        raise RuntimeError(
            "SYK UI uyumluluk yolu işareti "
            "kaynak dosyada bulunamadı."
        )

    isaret_indeksi = kaynak.index(
        ISARET
    )

    sonraki_bolum = kaynak[
        isaret_indeksi:
    ]

    return_eslesmesi = re.search(
        r"""
        return\s+RedirectResponse\s*\(
        (?P<govde>.*?)
        \n\s{8}\)
        """,
        sonraki_bolum,
        flags=(
            re.DOTALL
            | re.VERBOSE
        ),
    )

    if not return_eslesmesi:
        raise RuntimeError(
            "Uyumluluk yönlendirme bloğu "
            "bulunamadı."
        )

    blok = return_eslesmesi.group(
        0
    )

    url_eslesmesi = re.search(
        r"""url\s*=\s*["']([^"']+)["']""",
        blok,
    )

    eski_hedef = (
        url_eslesmesi.group(
            1
        )
        if url_eslesmesi
        else None
    )

    if eski_hedef == yeni_hedef:
        return (
            False,
            eski_hedef,
        )

    if not url_eslesmesi:
        raise RuntimeError(
            "RedirectResponse url değeri "
            "bulunamadı."
        )

    yeni_blok = (
        blok[
            :url_eslesmesi.start(
                1
            )
        ]
        + yeni_hedef
        + blok[
            url_eslesmesi.end(
                1
            ):
        ]
    )

    yeni_sonraki_bolum = (
        sonraki_bolum.replace(
            blok,
            yeni_blok,
            1,
        )
    )

    yeni_kaynak = (
        kaynak[:isaret_indeksi]
        + yeni_sonraki_bolum
    )

    ast.parse(
        yeni_kaynak,
        filename=str(
            KAYNAK
        ),
    )

    KAYNAK.write_text(
        yeni_kaynak,
        encoding="utf-8",
    )

    return (
        True,
        eski_hedef,
    )


def main() -> int:
    gercek_yol, kayitlar = (
        gercek_ui_yolunu_bul()
    )

    degisti, eski_hedef = (
        uyumluluk_hedefini_guncelle(
            gercek_yol
        )
    )

    sonuc = {
        "gercek_ui_yolu": gercek_yol,
        "eski_ui_hedefi": eski_hedef,
        "kaynak_degisti": degisti,
        "taranan_yol_sayisi": len(
            kayitlar
        ),
        "yollar": kayitlar,
    }

    SONUC_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SONUC_JSON.write_text(
        json.dumps(
            sonuc,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    satirlar = [
        "SPR-011 PAKET-012",
        "GERCEK UI YOLU TARAMA VE ONARIM",
        "",
        (
            "GERCEK_UI_YOLU="
            f"{gercek_yol}"
        ),
        (
            "ESKI_UI_HEDEFI="
            f"{eski_hedef}"
        ),
        (
            "KAYNAK_DEGISTI="
            f"{degisti}"
        ),
        (
            "TARANAN_YOL_SAYISI="
            f"{len(kayitlar)}"
        ),
        "",
        "=== YOL PUANLARI ===",
    ]

    for kayit in kayitlar:
        satirlar.append(
            " | ".join(
                (
                    (
                        "YOL="
                        f"{kayit.get('yol')}"
                    ),
                    (
                        "DURUM="
                        f"{kayit.get('durum')}"
                    ),
                    (
                        "HTML="
                        f"{kayit.get('html_mi')}"
                    ),
                    (
                        "ETIKET="
                        f"{kayit.get('etiket_sayisi')}"
                    ),
                    (
                        "BUTTON="
                        f"{kayit.get('button_sayisi')}"
                    ),
                    (
                        "ARIA_BUTTON="
                        f"{kayit.get('aria_button_sayisi')}"
                    ),
                    (
                        "UZUNLUK="
                        f"{kayit.get('uzunluk')}"
                    ),
                    (
                        "PUAN="
                        f"{kayit.get('puan')}"
                    ),
                )
            )
        )

    SONUC_TXT.write_text(
        "\n".join(
            satirlar
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "GERCEK_UI_YOLU_BULUNDU="
        + gercek_yol
    )

    print(
        "ESKI_UI_HEDEFI="
        + str(
            eski_hedef
        )
    )

    print(
        "UI_UYUMLULUK_HEDEFI_GUNCELLENDI="
        + str(
            degisti
        )
    )

    print(
        "TARANAN_YOL_SAYISI="
        + str(
            len(
                kayitlar
            )
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
