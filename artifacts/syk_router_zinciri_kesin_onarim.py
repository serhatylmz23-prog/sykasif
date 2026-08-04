from __future__ import annotations

import ast
import re
from pathlib import Path


API_ROUTES = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/api_routes.py"
)

ANA_SUNUCU = Path(
    "src/syk_simulasyon/"
    "runtime_ui_sunucusu.py"
)


ALT_ROUTERLAR = (
    (
        "from .mobile_control_routes import "
        "router as mobile_control_router",
        "mobile_control_router",
    ),
    (
        "from .mobile_device_routes import "
        "router as mobile_device_router",
        "mobile_device_router",
    ),
    (
        "from .mobile_offline_routes import "
        "router as mobile_offline_router",
        "mobile_offline_router",
    ),
    (
        "from .mobile_sensor_routes import "
        "router as mobile_sensor_router",
        "mobile_sensor_router",
    ),
    (
        "from .kasif_icon_routes import "
        "router as kasif_icon_router",
        "kasif_icon_router",
    ),
    (
        "from syk_jarmin.jarmin_integration_api "
        "import router as jarmin_integration_router",
        "jarmin_integration_router",
    ),
)


KOPRU_BASLANGIC = (
    "# === SYK_KESIN_ROUTER_KOPRUSU_BASLANGIC ==="
)

KOPRU_BITIS = (
    "# === SYK_KESIN_ROUTER_KOPRUSU_BITIS ==="
)


def parse(
    yol: Path,
    kaynak: str,
) -> ast.Module:
    return ast.parse(
        kaynak,
        filename=str(yol),
    )


def bosluksuz(
    kaynak: str,
) -> str:
    return "".join(
        kaynak.split()
    )


def import_sonu(
    agac: ast.Module,
) -> int:
    """
    Yalnız modül seviyesindeki bütün importların
    gerçek bitiş satırının en büyüğünü döndürür.
    """

    importlar = [
        dugum
        for dugum in agac.body
        if isinstance(
            dugum,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        )
    ]

    if importlar:
        return max(
            dugum.end_lineno
            or dugum.lineno
            for dugum in importlar
        )

    if (
        agac.body
        and isinstance(
            agac.body[0],
            ast.Expr,
        )
        and isinstance(
            agac.body[0].value,
            ast.Constant,
        )
        and isinstance(
            agac.body[0].value.value,
            str,
        )
    ):
        return (
            agac.body[0].end_lineno
            or agac.body[0].lineno
        )

    return 0


def importlari_guvenli_ekle(
    *,
    yol: Path,
    kaynak: str,
    importlar: tuple[str, ...],
) -> str:
    eksikler = tuple(
        ifade
        for ifade in importlar
        if ifade not in kaynak
    )

    if not eksikler:
        return kaynak

    agac = parse(
        yol,
        kaynak,
    )

    indeks = import_sonu(
        agac
    )

    satirlar = kaynak.splitlines(
        keepends=True
    )

    blok = (
        "\n".join(
            eksikler
        )
        + "\n"
    )

    # end_lineno 1 tabanlı, liste indeksi ise 0 tabanlıdır.
    # Bu nedenle doğrudan indeks kullanmak import bloğunun
    # tamamından sonraya ekler.
    satirlar.insert(
        indeks,
        blok,
    )

    sonuc = "".join(
        satirlar
    )

    parse(
        yol,
        sonuc,
    )

    return sonuc


# -------------------------------------------------
# A. API_ROUTES ALT ROUTER ZİNCİRİ
# -------------------------------------------------

api_metin = API_ROUTES.read_text(
    encoding="utf-8"
)

parse(
    API_ROUTES,
    api_metin,
)

api_metin = importlari_guvenli_ekle(
    yol=API_ROUTES,
    kaynak=api_metin,
    importlar=tuple(
        ifade
        for ifade, _
        in ALT_ROUTERLAR
    ),
)

api_siki = bosluksuz(
    api_metin
)

kayitlar = []

for _, router_adi in ALT_ROUTERLAR:
    imza = (
        "router.include_router("
        f"{router_adi}"
        ")"
    )

    if imza not in api_siki:
        kayitlar.append(
            "\n".join(
                (
                    "router.include_router(",
                    f"    {router_adi}",
                    ")",
                )
            )
        )

if kayitlar:
    api_metin = (
        api_metin.rstrip()
        + "\n\n"
        + "\n\n".join(
            kayitlar
        )
        + "\n"
    )

parse(
    API_ROUTES,
    api_metin,
)

api_siki = bosluksuz(
    api_metin
)

if (
    "router.include_router(router)"
    in api_siki
):
    raise RuntimeError(
        "Ana UI router kendi kendisine bağlanmış."
    )

for import_ifadesi, router_adi in ALT_ROUTERLAR:
    import_imzasi = bosluksuz(
        import_ifadesi
    )

    kayit_imzasi = (
        "router.include_router("
        f"{router_adi}"
        ")"
    )

    import_sayisi = api_siki.count(
        import_imzasi
    )

    kayit_sayisi = api_siki.count(
        kayit_imzasi
    )

    if import_sayisi != 1:
        raise RuntimeError(
            f"{router_adi} import sayısı: "
            f"{import_sayisi}"
        )

    if kayit_sayisi != 1:
        raise RuntimeError(
            f"{router_adi} router kayıt sayısı: "
            f"{kayit_sayisi}"
        )

API_ROUTES.write_text(
    api_metin,
    encoding="utf-8",
)

parse(
    API_ROUTES,
    API_ROUTES.read_text(
        encoding="utf-8"
    ),
)


# -------------------------------------------------
# B. GERÇEK FASTAPI APP KÖPRÜSÜ
# -------------------------------------------------

sunucu_metin = ANA_SUNUCU.read_text(
    encoding="utf-8"
)

parse(
    ANA_SUNUCU,
    sunucu_metin,
)


# Önceki iki köprü denemesini temizle.
eski_isaretler = (
    (
        "# === SYK_RUNTIME_ROUTER_KOPRUSU_BASLANGIC ===",
        "# === SYK_RUNTIME_ROUTER_KOPRUSU_BITIS ===",
    ),
    (
        KOPRU_BASLANGIC,
        KOPRU_BITIS,
    ),
)

for baslangic_isareti, bitis_isareti in eski_isaretler:
    while (
        baslangic_isareti in sunucu_metin
        and bitis_isareti in sunucu_metin
    ):
        baslangic = sunucu_metin.index(
            baslangic_isareti
        )

        bitis = (
            sunucu_metin.index(
                bitis_isareti,
                baslangic,
            )
            + len(
                bitis_isareti
            )
        )

        sunucu_metin = (
            sunucu_metin[:baslangic].rstrip()
            + "\n"
            + sunucu_metin[bitis:].lstrip()
        )


# Önceki doğrudan importları temizle.
sunucu_metin = re.sub(
    (
        r"(?m)^from \.syk_ui_runtime\.api_routes "
        r"import router as syk_ui_router\s*\n?"
    ),
    "",
    sunucu_metin,
)

sunucu_metin = re.sub(
    (
        r"(?m)^from \.syk_ui_runtime\."
        r"syfinans_runtime_routes "
        r"import finans_router\s*\n?"
    ),
    "",
    sunucu_metin,
)


# Önceki doğrudan include kayıtlarını temizle.
sunucu_metin = re.sub(
    (
        r"(?ms)^[ \t]*app\.include_router\(\s*"
        r"syk_ui_router\s*\)\s*\n?"
    ),
    "",
    sunucu_metin,
)

sunucu_metin = re.sub(
    (
        r"(?ms)^[ \t]*app\.include_router\(\s*"
        r"finans_router\s*\)\s*\n?"
    ),
    "",
    sunucu_metin,
)


kopru = '''
# === SYK_KESIN_ROUTER_KOPRUSU_BASLANGIC ===

from .syk_ui_runtime.api_routes import (
    router as syk_ui_router,
)

from .syk_ui_runtime.syfinans_runtime_routes import (
    finans_router,
)


def _syk_router_koku_var_mi(
    uygulama,
    kok: str,
) -> bool:
    return any(
        str(
            getattr(
                route,
                "path",
                "",
            )
        ) == kok
        or str(
            getattr(
                route,
                "path",
                "",
            )
        ).startswith(
            kok.rstrip("/") + "/"
        )
        for route in uygulama.routes
    )


if not _syk_router_koku_var_mi(
    app,
    "/api/syk-ui",
):
    app.include_router(
        syk_ui_router
    )


if not _syk_router_koku_var_mi(
    app,
    "/syfinans",
):
    app.include_router(
        finans_router
    )

# === SYK_KESIN_ROUTER_KOPRUSU_BITIS ===
'''

sunucu_metin = (
    sunucu_metin.rstrip()
    + "\n\n"
    + kopru.strip()
    + "\n"
)

parse(
    ANA_SUNUCU,
    sunucu_metin,
)

if sunucu_metin.count(
    KOPRU_BASLANGIC
) != 1:
    raise RuntimeError(
        "Kesin köprü başlangıç sayısı hatalı."
    )

if sunucu_metin.count(
    KOPRU_BITIS
) != 1:
    raise RuntimeError(
        "Kesin köprü bitiş sayısı hatalı."
    )

ANA_SUNUCU.write_text(
    sunucu_metin,
    encoding="utf-8",
)

parse(
    ANA_SUNUCU,
    ANA_SUNUCU.read_text(
        encoding="utf-8"
    ),
)


print(
    "SYK_ROUTER_ZINCIRI_KESIN_ONARIM_OK"
)

for _, router_adi in ALT_ROUTERLAR:
    print(
        "ALT_ROUTER",
        router_adi,
        "IMPORT",
        1,
        "KAYIT",
        1,
    )

print(
    "GERCEK_APP_KOPRU",
    1,
)