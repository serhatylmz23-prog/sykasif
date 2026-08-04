from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


RUNTIME = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime"
)

API_ROUTES = (
    RUNTIME
    / "api_routes.py"
)


@dataclass(frozen=True, slots=True)
class RouterHedefi:
    modul: str
    kaynak_adi: str
    takma_ad: str


HEDEFLER = (
    RouterHedefi(
        modul="mobile_control_routes",
        kaynak_adi="router",
        takma_ad="mobile_control_router",
    ),
    RouterHedefi(
        modul="mobile_device_routes",
        kaynak_adi="router",
        takma_ad="mobile_device_router",
    ),
    RouterHedefi(
        modul="mobile_offline_routes",
        kaynak_adi="router",
        takma_ad="mobile_offline_router",
    ),
    RouterHedefi(
        modul="mobile_sensor_routes",
        kaynak_adi="router",
        takma_ad="mobile_sensor_router",
    ),
    RouterHedefi(
        modul="kasif_icon_routes",
        kaynak_adi="router",
        takma_ad="kasif_icon_router",
    ),
)


def parse(
    kaynak: str,
) -> ast.Module:
    return ast.parse(
        kaynak,
        filename=str(
            API_ROUTES
        ),
    )


def bosluksuz(
    kaynak: str,
) -> str:
    return "".join(
        kaynak.split()
    )


def modul_import_indeksi(
    agac: ast.Module,
) -> int:
    son = 0

    for dugum in agac.body:
        if (
            isinstance(
                dugum,
                ast.Expr,
            )
            and isinstance(
                dugum.value,
                ast.Constant,
            )
            and isinstance(
                dugum.value.value,
                str,
            )
        ):
            son = max(
                son,
                dugum.end_lineno
                or dugum.lineno,
            )
            continue

        if isinstance(
            dugum,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            son = max(
                son,
                dugum.end_lineno
                or dugum.lineno,
            )
            continue

        if son:
            break

    return son


def router_nesnesi_var_mi(
    yol: Path,
    beklenen_ad: str,
) -> bool:
    kaynak = yol.read_text(
        encoding="utf-8",
        errors="replace",
    )

    agac = ast.parse(
        kaynak,
        filename=str(yol),
    )

    for dugum in agac.body:
        if not isinstance(
            dugum,
            ast.Assign,
        ):
            continue

        for hedef in dugum.targets:
            if (
                isinstance(
                    hedef,
                    ast.Name,
                )
                and hedef.id
                == beklenen_ad
            ):
                return True

    return False


# Kaynak router dosyalarını doğrula.
for hedef in HEDEFLER:
    yol = (
        RUNTIME
        / f"{hedef.modul}.py"
    )

    if not yol.is_file():
        raise FileNotFoundError(
            yol
        )

    if not router_nesnesi_var_mi(
        yol,
        hedef.kaynak_adi,
    ):
        raise RuntimeError(
            f"{yol} içinde "
            f"{hedef.kaynak_adi} "
            "bulunamadı."
        )


metin = API_ROUTES.read_text(
    encoding="utf-8"
)

parse(
    metin
)


# Önceki hatalı, aynı isimli router importlarını temizle.
for hedef in HEDEFLER:
    desenler = (
        (
            rf"(?m)^from \.{re.escape(hedef.modul)} "
            rf"import {re.escape(hedef.kaynak_adi)}"
            rf"\s*\n?"
        ),
        (
            rf"(?ms)^from \.{re.escape(hedef.modul)} "
            rf"import \(\s*"
            rf"{re.escape(hedef.kaynak_adi)}"
            rf",?\s*\)\s*\n?"
        ),
    )

    for desen in desenler:
        metin = re.sub(
            desen,
            "",
            metin,
        )


# Hatalı router.include_router(router) kayıtlarını temizle.
metin = re.sub(
    (
        r"(?ms)^[ \t]*router"
        r"\.include_router\(\s*"
        r"router\s*\)\s*\n?"
    ),
    "",
    metin,
)


agac = parse(
    metin
)

satirlar = metin.splitlines(
    keepends=True
)

ekleme_indeksi = modul_import_indeksi(
    agac
)

importlar = []

for hedef in HEDEFLER:
    beklenen = (
        f"from .{hedef.modul} import "
        f"{hedef.kaynak_adi} as "
        f"{hedef.takma_ad}"
    )

    if beklenen not in metin:
        importlar.append(
            beklenen
        )

if importlar:
    satirlar.insert(
        ekleme_indeksi,
        "\n".join(
            importlar
        )
        + "\n",
    )

    metin = "".join(
        satirlar
    )


parse(
    metin
)

siki = bosluksuz(
    metin
)

kayit_bloklari = []

for hedef in HEDEFLER:
    imza = (
        "router.include_router("
        f"{hedef.takma_ad}"
        ")"
    )

    if imza not in siki:
        kayit_bloklari.append(
            "\n".join(
                (
                    "router.include_router(",
                    f"    {hedef.takma_ad}",
                    ")",
                )
            )
        )

if kayit_bloklari:
    metin = (
        metin.rstrip()
        + "\n\n"
        + "\n\n".join(
            kayit_bloklari
        )
        + "\n"
    )


parse(
    metin
)

siki = bosluksuz(
    metin
)

if (
    "router.include_router(router)"
    in siki
):
    raise RuntimeError(
        "Ana router kendi kendisine "
        "bağlanmış durumda."
    )


for hedef in HEDEFLER:
    import_imzasi = (
        f"from.{hedef.modul}"
        f"import{hedef.kaynak_adi}"
        f"as{hedef.takma_ad}"
    )

    kayit_imzasi = (
        "router.include_router("
        f"{hedef.takma_ad}"
        ")"
    )

    import_sayisi = siki.count(
        import_imzasi
    )

    kayit_sayisi = siki.count(
        kayit_imzasi
    )

    if import_sayisi != 1:
        raise RuntimeError(
            f"{hedef.takma_ad} import "
            f"sayısı hatalı: "
            f"{import_sayisi}"
        )

    if kayit_sayisi != 1:
        raise RuntimeError(
            f"{hedef.takma_ad} kayıt "
            f"sayısı hatalı: "
            f"{kayit_sayisi}"
        )


API_ROUTES.write_text(
    metin,
    encoding="utf-8",
)

parse(
    API_ROUTES.read_text(
        encoding="utf-8"
    )
)


print(
    "SYK_ALT_ROUTER_ZINCIRI_PATCH_OK"
)

for hedef in HEDEFLER:
    print(
        "ALT_ROUTER",
        hedef.takma_ad,
        "IMPORT",
        1,
        "KAYIT",
        1,
    )