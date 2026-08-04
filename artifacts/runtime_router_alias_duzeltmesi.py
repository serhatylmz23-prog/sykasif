from __future__ import annotations

import ast
from pathlib import Path


API_ROUTES = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime/api_routes.py"
)

ANA_SUNUCU = Path(
    "src/syk_simulasyon/"
    "runtime_ui_sunucusu.py"
)


API_IMPORTLARI = (
    (
        "from .kasif_icon_routes import "
        "router as kasif_icon_router",
        "kasif_icon_router",
    ),
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
        "from syk_jarmin.jarmin_integration_api "
        "import router as jarmin_integration_router",
        "jarmin_integration_router",
    ),
)

FINANS_IMPORT = (
    "from .syk_ui_runtime.syfinans_runtime_routes "
    "import finans_router"
)


def dogrula(
    yol: Path,
    metin: str,
) -> ast.Module:
    return ast.parse(
        metin,
        filename=str(yol),
    )


def modul_import_satiri(
    agac: ast.Module,
) -> int:
    """
    Dönüş değeri splitlines listesine doğrudan
    ekleme indeksi olarak kullanılır.
    """
    son_satir = 0

    for dugum in agac.body:
        if isinstance(
            dugum,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            son_satir = max(
                son_satir,
                dugum.end_lineno
                or dugum.lineno,
            )
            continue

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
            son_satir = max(
                son_satir,
                dugum.end_lineno
                or dugum.lineno,
            )
            continue

        if son_satir:
            break

    return son_satir


def importlari_ekle(
    *,
    yol: Path,
    metin: str,
    importlar: tuple[str, ...],
) -> str:
    eksik = tuple(
        ifade
        for ifade in importlar
        if ifade not in metin
    )

    if not eksik:
        return metin

    agac = dogrula(
        yol,
        metin,
    )

    ekleme_indeksi = (
        modul_import_satiri(
            agac
        )
    )

    satirlar = metin.splitlines(
        keepends=True
    )

    blok = (
        "\n".join(
            eksik
        )
        + "\n"
    )

    satirlar.insert(
        ekleme_indeksi,
        blok,
    )

    sonuc = "".join(
        satirlar
    )

    dogrula(
        yol,
        sonuc,
    )

    return sonuc


def router_kayitli_mi(
    metin: str,
    router_adi: str,
    sahip: str,
) -> bool:
    bosluksuz = "".join(
        metin.split()
    )

    return (
        f"{sahip}.include_router("
        f"{router_adi})"
        in bosluksuz
    )


def routerlari_ekle(
    *,
    yol: Path,
    metin: str,
    sahip: str,
    routerlar: tuple[str, ...],
) -> str:
    eksik = tuple(
        router_adi
        for router_adi in routerlar
        if not router_kayitli_mi(
            metin,
            router_adi,
            sahip,
        )
    )

    if not eksik:
        return metin

    bloklar = []

    for router_adi in eksik:
        bloklar.append(
            "\n".join(
                (
                    f"{sahip}.include_router(",
                    f"    {router_adi}",
                    ")",
                )
            )
        )

    sonuc = (
        metin.rstrip()
        + "\n\n"
        + "\n\n".join(
            bloklar
        )
        + "\n"
    )

    dogrula(
        yol,
        sonuc,
    )

    return sonuc


# --------------------------------------------------
# API_ROUTES: MOBİL + JARMİN + KAŞİF İKONLARI
# --------------------------------------------------

api_metin = API_ROUTES.read_text(
    encoding="utf-8"
)

api_metin = importlari_ekle(
    yol=API_ROUTES,
    metin=api_metin,
    importlar=tuple(
        ifade
        for ifade, _
        in API_IMPORTLARI
    ),
)

api_metin = routerlari_ekle(
    yol=API_ROUTES,
    metin=api_metin,
    sahip="router",
    routerlar=tuple(
        router_adi
        for _, router_adi
        in API_IMPORTLARI
    ),
)

# Ana router kendi kendisine bağlanmamalı.
bosluksuz_api = "".join(
    api_metin.split()
)

if "router.include_router(router)" in bosluksuz_api:
    raise RuntimeError(
        "Ana APIRouter kendi kendisine bağlanmış."
    )

for _, router_adi in API_IMPORTLARI:
    sayi = bosluksuz_api.count(
        f"router.include_router({router_adi})"
    )

    if sayi != 1:
        raise RuntimeError(
            f"{router_adi} kayıt sayısı "
            f"beklenenden farklı: {sayi}"
        )

API_ROUTES.write_text(
    api_metin,
    encoding="utf-8",
)

dogrula(
    API_ROUTES,
    API_ROUTES.read_text(
        encoding="utf-8"
    ),
)


# --------------------------------------------------
# ANA FASTAPI APP: SYFİNANS /syfinans
# --------------------------------------------------

sunucu_metin = ANA_SUNUCU.read_text(
    encoding="utf-8"
)

sunucu_metin = importlari_ekle(
    yol=ANA_SUNUCU,
    metin=sunucu_metin,
    importlar=(
        FINANS_IMPORT,
    ),
)

sunucu_agac = dogrula(
    ANA_SUNUCU,
    sunucu_metin,
)

app_var = any(
    isinstance(
        dugum,
        (
            ast.Assign,
            ast.AnnAssign,
        ),
    )
    and (
        (
            isinstance(
                dugum,
                ast.Assign,
            )
            and any(
                isinstance(
                    hedef,
                    ast.Name,
                )
                and hedef.id == "app"
                for hedef in dugum.targets
            )
        )
        or (
            isinstance(
                dugum,
                ast.AnnAssign,
            )
            and isinstance(
                dugum.target,
                ast.Name,
            )
            and dugum.target.id == "app"
        )
    )
    for dugum in sunucu_agac.body
)

if not app_var:
    raise RuntimeError(
        "runtime_ui_sunucusu.py içinde "
        "modül seviyesinde app bulunamadı."
    )

sunucu_metin = routerlari_ekle(
    yol=ANA_SUNUCU,
    metin=sunucu_metin,
    sahip="app",
    routerlar=(
        "finans_router",
    ),
)

bosluksuz_sunucu = "".join(
    sunucu_metin.split()
)

finans_kayit_sayisi = (
    bosluksuz_sunucu.count(
        "app.include_router(finans_router)"
    )
)

if finans_kayit_sayisi != 1:
    raise RuntimeError(
        "SyFinans app router kayıt sayısı "
        f"beklenenden farklı: "
        f"{finans_kayit_sayisi}"
    )

ANA_SUNUCU.write_text(
    sunucu_metin,
    encoding="utf-8",
)

dogrula(
    ANA_SUNUCU,
    ANA_SUNUCU.read_text(
        encoding="utf-8"
    ),
)


print(
    "RUNTIME_ROUTER_ALIAS_DUZELTMESI_OK"
)

for _, router_adi in API_IMPORTLARI:
    print(
        "UI_ROUTER",
        router_adi,
    )

print(
    "APP_ROUTER",
    "finans_router",
)

print(
    "KENDINI_BAGLAYAN_ROUTER",
    0,
)