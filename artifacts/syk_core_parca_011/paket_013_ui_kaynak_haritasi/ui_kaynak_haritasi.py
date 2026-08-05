from __future__ import annotations

import ast
import json
import re
from pathlib import Path


KOKLER = (
    Path("src/syk_simulasyon"),
    Path("src/syk_ui"),
)

RAPOR = Path(
    "artifacts/syk_core_parca_011/"
    "paket_013_ui_kaynak_haritasi/"
    "UI_KAYNAK_HARITASI.txt"
)

JSON_CIKTI = Path(
    "artifacts/syk_core_parca_011/"
    "paket_013_ui_kaynak_haritasi/"
    "ui_kaynak_haritasi.json"
)

ARAMALAR = (
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
    "syk-ui-screen",
    "runtime/html",
    "HTMLResponse",
    "TemplateResponse",
    "FileResponse",
    "StaticFiles",
    "include_router",
    "include_in_schema",
)

UZANTILAR = {
    ".py",
    ".html",
    ".htm",
    ".js",
    ".css",
    ".json",
}


def dosyalari_bul() -> list[Path]:
    dosyalar: list[Path] = []

    for kok in KOKLER:
        if not kok.exists():
            continue

        for dosya in kok.rglob("*"):
            if (
                dosya.is_file()
                and dosya.suffix.lower() in UZANTILAR
                and "__pycache__" not in dosya.parts
            ):
                dosyalar.append(dosya)

    return sorted(
        set(dosyalar)
    )


def metin_oku(
    dosya: Path,
) -> str:
    for kodlama in (
        "utf-8-sig",
        "utf-8",
        "cp1254",
    ):
        try:
            return dosya.read_text(
                encoding=kodlama
            )
        except UnicodeDecodeError:
            continue

    return dosya.read_text(
        encoding="utf-8",
        errors="replace",
    )


def python_route_bilgileri(
    dosya: Path,
    kaynak: str,
) -> list[dict]:
    try:
        agac = ast.parse(
            kaynak,
            filename=str(dosya),
        )
    except SyntaxError:
        return []

    sonuclar: list[dict] = []

    for dugum in ast.walk(agac):
        if not isinstance(
            dugum,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        dekoratorlar: list[str] = []

        for dekorator in dugum.decorator_list:
            try:
                dekoratorlar.append(
                    ast.unparse(dekorator)
                )
            except Exception:
                continue

        ilgili = [
            dekorator
            for dekorator in dekoratorlar
            if any(
                isaret in dekorator
                for isaret in (
                    ".get(",
                    ".post(",
                    ".route(",
                    ".api_route(",
                )
            )
        ]

        if ilgili:
            sonuclar.append(
                {
                    "fonksiyon": dugum.name,
                    "satir": dugum.lineno,
                    "dekoratorlar": ilgili,
                }
            )

    return sonuclar


def main() -> int:
    dosyalar = dosyalari_bul()

    eslesmeler: list[dict] = []
    route_kayitlari: list[dict] = []
    html_adaylari: list[dict] = []

    for dosya in dosyalar:
        kaynak = metin_oku(dosya)
        satirlar = kaynak.splitlines()

        dosya_eslesmeleri = []

        for satir_no, satir in enumerate(
            satirlar,
            start=1,
        ):
            bulunanlar = [
                arama
                for arama in ARAMALAR
                if arama.casefold()
                in satir.casefold()
            ]

            if bulunanlar:
                kayit = {
                    "dosya": dosya.as_posix(),
                    "satir": satir_no,
                    "bulunanlar": bulunanlar,
                    "icerik": satir.strip()[:1000],
                }

                eslesmeler.append(kayit)
                dosya_eslesmeleri.append(kayit)

        if dosya.suffix.lower() == ".py":
            routes = python_route_bilgileri(
                dosya,
                kaynak,
            )

            if routes:
                route_kayitlari.append(
                    {
                        "dosya": dosya.as_posix(),
                        "routes": routes,
                    }
                )

        bilimsel_sayi = sum(
            1
            for etiket in ARAMALAR[:15]
            if etiket.casefold()
            in kaynak.casefold()
        )

        button_sayi = len(
            re.findall(
                r"<button\b",
                kaynak,
                flags=re.IGNORECASE,
            )
        )

        role_button_sayi = len(
            re.findall(
                r"""role\s*=\s*["']button["']""",
                kaynak,
                flags=re.IGNORECASE,
            )
        )

        if (
            bilimsel_sayi > 0
            or button_sayi > 0
            or role_button_sayi > 0
        ):
            html_adaylari.append(
                {
                    "dosya": dosya.as_posix(),
                    "bilimsel_etiket_sayisi": bilimsel_sayi,
                    "button_sayisi": button_sayi,
                    "role_button_sayisi": role_button_sayi,
                    "toplam_puan": (
                        bilimsel_sayi * 20
                        + button_sayi * 3
                        + role_button_sayi * 2
                    ),
                }
            )

    html_adaylari.sort(
        key=lambda kayit: (
            kayit["toplam_puan"],
            kayit["bilimsel_etiket_sayisi"],
            kayit["button_sayisi"],
        ),
        reverse=True,
    )

    sonuc = {
        "incelenen_dosya_sayisi": len(dosyalar),
        "eslesme_sayisi": len(eslesmeler),
        "route_dosyasi_sayisi": len(route_kayitlari),
        "html_adayi_sayisi": len(html_adaylari),
        "en_guclu_ui_adaylari": html_adaylari[:30],
        "route_kayitlari": route_kayitlari,
        "eslesmeler": eslesmeler,
    }

    JSON_CIKTI.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    JSON_CIKTI.write_text(
        json.dumps(
            sonuc,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    satirlar = [
        "SPR-011 PAKET-013",
        "UI KAYNAK HARITASI",
        "",
        f"INCELENEN_DOSYA_SAYISI={len(dosyalar)}",
        f"ESLESME_SAYISI={len(eslesmeler)}",
        f"ROUTE_DOSYASI_SAYISI={len(route_kayitlari)}",
        f"UI_ADAYI_SAYISI={len(html_adaylari)}",
        "",
        "=== EN GUCLU UI ADAYLARI ===",
    ]

    for aday in html_adaylari[:30]:
        satirlar.append(
            " | ".join(
                (
                    f"DOSYA={aday['dosya']}",
                    f"BILIMSEL={aday['bilimsel_etiket_sayisi']}",
                    f"BUTTON={aday['button_sayisi']}",
                    f"ROLE_BUTTON={aday['role_button_sayisi']}",
                    f"PUAN={aday['toplam_puan']}",
                )
            )
        )

    satirlar.extend(
        [
            "",
            "=== ROUTE KAYITLARI ===",
        ]
    )

    for kayit in route_kayitlari:
        satirlar.append(
            f"DOSYA={kayit['dosya']}"
        )

        for route in kayit["routes"]:
            satirlar.append(
                (
                    f"  SATIR={route['satir']} "
                    f"FONKSIYON={route['fonksiyon']} "
                    f"DEKORATOR={route['dekoratorlar']}"
                )
            )

    satirlar.extend(
        [
            "",
            "=== JEOLOJI VE UI ESLESMELERI ===",
        ]
    )

    for kayit in eslesmeler:
        if any(
            deger in kayit["bulunanlar"]
            for deger in (
                "Jeoloji",
                "syk-ui-screen",
                "runtime/html",
                "HTMLResponse",
                "TemplateResponse",
                "FileResponse",
            )
        ):
            satirlar.append(
                (
                    f"DOSYA={kayit['dosya']} "
                    f"SATIR={kayit['satir']} "
                    f"BULUNAN={kayit['bulunanlar']} "
                    f"ICERIK={kayit['icerik']}"
                )
            )

    RAPOR.write_text(
        "\n".join(satirlar)
        + "\n",
        encoding="utf-8",
    )

    print("UI_KAYNAK_HARITASI_TAMAMLANDI")
    print(
        "INCELENEN_DOSYA_SAYISI="
        + str(len(dosyalar))
    )
    print(
        "ESLESME_SAYISI="
        + str(len(eslesmeler))
    )
    print(
        "UI_ADAYI_SAYISI="
        + str(len(html_adaylari))
    )

    for sira, aday in enumerate(
        html_adaylari[:10],
        start=1,
    ):
        print(
            f"ADAY_{sira}="
            f"{aday['dosya']}|"
            f"BILIMSEL={aday['bilimsel_etiket_sayisi']}|"
            f"BUTTON={aday['button_sayisi']}|"
            f"PUAN={aday['toplam_puan']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
