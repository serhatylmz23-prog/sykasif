from __future__ import annotations

import ast
from pathlib import Path


DOSYA = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

IMPORT_ISARETI = (
    "# SYK_UGR_DOGRUDAN_ROUTER_IMPORT"
)

ROUTE_ISARETI = (
    "# SYK_UGR_DOGRUDAN_ROUTE_BAGLANTISI"
)

IMPORT_BLOGU = [
    IMPORT_ISARETI,
    "from syk_simulasyon.syk_ui_runtime.ugr_runtime_routes import (",
    "    ugr_router as syk_ugr_router,",
    ")",
]

TERMINAL_BLOGU = (
    "    # SYK_TERMINAL_FINANS_DOGRUDAN_ROUTE_BAGLANTISI\n"
    "    mevcut_yollar = {\n"
    '        getattr(route, "path", None)\n'
    "        for route in uygulama.router.routes\n"
    "    }\n"
    "\n"
    "    for route in syk_terminal_router.routes:\n"
    '        if getattr(route, "path", None) not in mevcut_yollar:\n'
    "            uygulama.router.routes.append(route)\n"
)

UGR_BLOGU = (
    "\n"
    "    # SYK_UGR_DOGRUDAN_ROUTE_BAGLANTISI\n"
    "    mevcut_yollar = {\n"
    '        getattr(route, "path", None)\n'
    "        for route in uygulama.router.routes\n"
    "    }\n"
    "\n"
    "    for route in syk_ugr_router.routes:\n"
    '        if getattr(route, "path", None) not in mevcut_yollar:\n'
    "            uygulama.router.routes.append(route)\n"
)


def import_ekle(
    kaynak: str,
) -> tuple[str, bool]:
    if (
        IMPORT_ISARETI in kaynak
        or "ugr_router as syk_ugr_router" in kaynak
    ):
        return kaynak, False

    agac = ast.parse(
        kaynak,
        filename=str(DOSYA),
    )

    son_import_satiri = 0

    for dugum in agac.body:
        if isinstance(
            dugum,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            son_import_satiri = max(
                son_import_satiri,
                int(
                    getattr(
                        dugum,
                        "end_lineno",
                        dugum.lineno,
                    )
                ),
            )

    if son_import_satiri == 0:
        raise RuntimeError(
            "Üst seviye import bölümü bulunamadı."
        )

    satirlar = kaynak.splitlines()

    yeni_satirlar = (
        satirlar[:son_import_satiri]
        + [""]
        + IMPORT_BLOGU
        + [""]
        + satirlar[son_import_satiri:]
    )

    return (
        "\n".join(yeni_satirlar) + "\n",
        True,
    )


def route_ekle(
    kaynak: str,
) -> tuple[str, bool]:
    if ROUTE_ISARETI in kaynak:
        return kaynak, False

    if TERMINAL_BLOGU not in kaynak:
        raise RuntimeError(
            "Terminal doğrudan route bağlantı bloğu bulunamadı."
        )

    return (
        kaynak.replace(
            TERMINAL_BLOGU,
            TERMINAL_BLOGU + UGR_BLOGU,
            1,
        ),
        True,
    )


def main() -> int:
    kaynak = DOSYA.read_text(
        encoding="utf-8-sig"
    )

    kaynak, import_eklendi = import_ekle(
        kaynak
    )

    kaynak, route_eklendi = route_ekle(
        kaynak
    )

    ast.parse(
        kaynak,
        filename=str(DOSYA),
    )

    if kaynak.count(
        "ugr_router as syk_ugr_router"
    ) != 1:
        raise RuntimeError(
            "UGR router import sayısı bir değil."
        )

    if kaynak.count(
        ROUTE_ISARETI
    ) != 1:
        raise RuntimeError(
            "UGR doğrudan route bağlantı sayısı bir değil."
        )

    DOSYA.write_text(
        kaynak,
        encoding="utf-8",
    )

    print(
        "UGR_ROUTER_IMPORT_EKLENDI="
        + str(import_eklendi)
    )

    print(
        "UGR_ROUTE_BAGLANTISI_EKLENDI="
        + str(route_eklendi)
    )

    print(
        "UGR_IMPORT_VE_ROUTE_PATCH_TAMAMLANDI"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
