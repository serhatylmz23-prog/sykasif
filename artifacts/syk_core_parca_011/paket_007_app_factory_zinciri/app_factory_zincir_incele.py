from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
SRC = ROOT / "src"
HEDEF_MODUL = "syk_simulasyon.runtime_ui_sunucusu"

ANAHTAR_KELIMELER = {
    "FastAPI",
    "Starlette",
    "APIRouter",
    "include_router",
    "create_app",
    "build_app",
    "get_app",
    "make_app",
    "application",
    "uygulama",
    "app",
    "factory",
    "uvicorn",
    "ASGI",
}


def nokta_adi(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        ust = nokta_adi(node.value)

        if ust:
            return f"{ust}.{node.attr}"

        return node.attr

    if isinstance(node, ast.Call):
        return nokta_adi(node.func)

    return None


def ilgi_var_mi(metin: str) -> bool:
    metin_kucuk = metin.lower()

    return any(
        kelime.lower() in metin_kucuk
        for kelime in ANAHTAR_KELIMELER
    )


def python_dosyalarini_tara() -> list[dict[str, Any]]:
    sonuclar: list[dict[str, Any]] = []

    for dosya in sorted(SRC.rglob("*.py")):
        if "__pycache__" in dosya.parts:
            continue

        try:
            kaynak = dosya.read_text(
                encoding="utf-8-sig"
            )

            agac = ast.parse(
                kaynak,
                filename=str(dosya),
            )

        except Exception as hata:
            sonuclar.append(
                {
                    "dosya": dosya.relative_to(ROOT).as_posix(),
                    "tur": "OKUMA_VEYA_AST_HATASI",
                    "satir": 0,
                    "icerik": f"{type(hata).__name__}: {hata}",
                }
            )
            continue

        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.Import):
                metin = ast.unparse(dugum)

                if ilgi_var_mi(metin):
                    sonuclar.append(
                        {
                            "dosya": dosya.relative_to(ROOT).as_posix(),
                            "tur": "IMPORT",
                            "satir": dugum.lineno,
                            "icerik": metin,
                        }
                    )

            elif isinstance(dugum, ast.ImportFrom):
                metin = ast.unparse(dugum)

                if ilgi_var_mi(metin):
                    sonuclar.append(
                        {
                            "dosya": dosya.relative_to(ROOT).as_posix(),
                            "tur": "IMPORT_FROM",
                            "satir": dugum.lineno,
                            "icerik": metin,
                        }
                    )

            elif isinstance(
                dugum,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                imza = ast.unparse(dugum).splitlines()[0]

                if ilgi_var_mi(
                    dugum.name + " " + imza
                ):
                    sonuclar.append(
                        {
                            "dosya": dosya.relative_to(ROOT).as_posix(),
                            "tur": "FONKSIYON",
                            "satir": dugum.lineno,
                            "icerik": imza,
                        }
                    )

            elif isinstance(
                dugum,
                (
                    ast.Assign,
                    ast.AnnAssign,
                ),
            ):
                try:
                    metin = ast.unparse(dugum)
                except Exception:
                    continue

                if ilgi_var_mi(metin):
                    sonuclar.append(
                        {
                            "dosya": dosya.relative_to(ROOT).as_posix(),
                            "tur": "ATAMA",
                            "satir": dugum.lineno,
                            "icerik": metin,
                        }
                    )

            elif isinstance(dugum, ast.Call):
                cagri_adi = nokta_adi(
                    dugum.func
                )

                if not cagri_adi:
                    continue

                metin = ast.unparse(
                    dugum
                )

                if ilgi_var_mi(
                    cagri_adi + " " + metin
                ):
                    sonuclar.append(
                        {
                            "dosya": dosya.relative_to(ROOT).as_posix(),
                            "tur": "CAGRI",
                            "satir": dugum.lineno,
                            "icerik": metin,
                        }
                    )

            elif isinstance(dugum, ast.Return):
                if dugum.value is None:
                    continue

                metin = ast.unparse(
                    dugum
                )

                if ilgi_var_mi(metin):
                    sonuclar.append(
                        {
                            "dosya": dosya.relative_to(ROOT).as_posix(),
                            "tur": "RETURN",
                            "satir": dugum.lineno,
                            "icerik": metin,
                        }
                    )

    return sonuclar


def runtime_modulunu_incele() -> list[dict[str, Any]]:
    modul = importlib.import_module(
        HEDEF_MODUL
    )

    sonuclar: list[dict[str, Any]] = []

    for ad in sorted(dir(modul)):
        if ad.startswith("_"):
            continue

        try:
            nesne = getattr(
                modul,
                ad,
            )
        except Exception as hata:
            sonuclar.append(
                {
                    "ad": ad,
                    "tur": "OKUMA_HATASI",
                    "callable": False,
                    "route_sayisi": None,
                    "ugr_route_sayisi": None,
                    "imza": f"{type(hata).__name__}: {hata}",
                }
            )
            continue

        tur_adi = (
            f"{type(nesne).__module__}."
            f"{type(nesne).__qualname__}"
        )

        callable_mi = callable(
            nesne
        )

        route_sayisi = None
        ugr_route_sayisi = None

        try:
            routes = getattr(
                nesne,
                "routes",
                None,
            )

            if (
                routes is not None
                and not isinstance(
                    routes,
                    property,
                )
            ):
                route_listesi = list(
                    routes
                )

                route_sayisi = len(
                    route_listesi
                )

                ugr_route_sayisi = sum(
                    1
                    for route in route_listesi
                    if str(
                        getattr(
                            route,
                            "path",
                            "",
                        )
                    ).startswith(
                        "/api/ugr"
                    )
                )

        except Exception:
            route_sayisi = None
            ugr_route_sayisi = None

        try:
            imza = str(
                inspect.signature(
                    nesne
                )
            )
        except Exception:
            imza = "-"

        ilgi = (
            ad.lower()
            in {
                "app",
                "application",
                "uygulama",
                "api",
                "server",
                "sunucu",
            }
            or "fastapi" in tur_adi.lower()
            or "starlette" in tur_adi.lower()
            or "asgi" in tur_adi.lower()
            or "router" in ad.lower()
            or route_sayisi is not None
        )

        if ilgi:
            sonuclar.append(
                {
                    "ad": ad,
                    "tur": tur_adi,
                    "callable": callable_mi,
                    "route_sayisi": route_sayisi,
                    "ugr_route_sayisi": ugr_route_sayisi,
                    "imza": imza,
                }
            )

    return sonuclar


def main() -> int:
    kaynak_sonuclari = python_dosyalarini_tara()
    runtime_sonuclari = runtime_modulunu_incele()

    rapor_satirlari = [
        "SPR-011 PAKET-007",
        "GERCEK APP FACTORY ZINCIR INCELEMESI",
        "",
        f"HEDEF_MODUL={HEDEF_MODUL}",
        f"KAYNAK_KAYIT_SAYISI={len(kaynak_sonuclari)}",
        f"RUNTIME_NESNE_SAYISI={len(runtime_sonuclari)}",
        "",
        "=== RUNTIME MODUL NESNELERI ===",
    ]

    for kayit in runtime_sonuclari:
        rapor_satirlari.append(
            " ".join(
                [
                    f"AD={kayit['ad']}",
                    f"TUR={kayit['tur']}",
                    f"CALLABLE={kayit['callable']}",
                    f"ROUTE_SAYISI={kayit['route_sayisi']}",
                    f"UGR_ROUTE_SAYISI={kayit['ugr_route_sayisi']}",
                    f"IMZA={kayit['imza']}",
                ]
            )
        )

    rapor_satirlari.extend(
        [
            "",
            "=== KAYNAK ZINCIRI ===",
        ]
    )

    for kayit in kaynak_sonuclari:
        rapor_satirlari.append(
            (
                f"{kayit['dosya']}:"
                f"{kayit['satir']} "
                f"[{kayit['tur']}] "
                f"{kayit['icerik']}"
            )
        )

    rapor = "\n".join(
        rapor_satirlari
    ) + "\n"

    rapor_yolu = (
        ROOT
        / "artifacts"
        / "syk_core_parca_011"
        / "paket_007_app_factory_zinciri"
        / "APP_FACTORY_ZINCIR_RAPORU.txt"
    )

    rapor_yolu.write_text(
        rapor,
        encoding="utf-8",
    )

    print(rapor)

    print(
        "APP_FACTORY_ZINCIR_INCELEMESI_TAMAMLANDI"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
