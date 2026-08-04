from __future__ import annotations

import ast
from pathlib import Path


HEDEF = Path(
    "src/syk_simulasyon/"
    "runtime_ui_sunucusu.py"
)

metin = HEDEF.read_text(
    encoding="utf-8"
)


UI_IMPORT = (
    "from .syk_ui_runtime.api_routes "
    "import router as syk_ui_router"
)

FINANS_IMPORT = (
    "from .syk_ui_runtime.syfinans_runtime_routes "
    "import finans_router"
)

UI_KAYDI = (
    "app.include_router(\n"
    "    syk_ui_router\n"
    ")"
)

FINANS_KAYDI = (
    "app.include_router(\n"
    "    finans_router\n"
    ")"
)


def ayrıştır(
    kaynak: str,
) -> ast.Module:
    return ast.parse(
        kaynak,
        filename=str(HEDEF),
    )


def bosluksuz(
    kaynak: str,
) -> str:
    return "".join(
        kaynak.split()
    )


def import_ekleme_indeksi(
    agac: ast.Module,
) -> int:
    son_satir = 0

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
            son_satir = max(
                son_satir,
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
            son_satir = max(
                son_satir,
                dugum.end_lineno
                or dugum.lineno,
            )
            continue

        if son_satir > 0:
            break

    return son_satir


def eksik_importlari_ekle(
    kaynak: str,
) -> str:
    eksikler = [
        ifade
        for ifade in (
            UI_IMPORT,
            FINANS_IMPORT,
        )
        if ifade not in kaynak
    ]

    if not eksikler:
        return kaynak

    agac = ayrıştır(
        kaynak
    )

    indeks = import_ekleme_indeksi(
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

    satirlar.insert(
        indeks,
        blok,
    )

    sonuc = "".join(
        satirlar
    )

    ayrıştır(
        sonuc
    )

    return sonuc


def app_atamasini_bul(
    agac: ast.Module,
) -> ast.Assign | ast.AnnAssign:
    adaylar = []

    for dugum in agac.body:
        if isinstance(
            dugum,
            ast.Assign,
        ):
            if any(
                isinstance(
                    hedef,
                    ast.Name,
                )
                and hedef.id == "app"
                for hedef in dugum.targets
            ):
                adaylar.append(
                    dugum
                )

        elif isinstance(
            dugum,
            ast.AnnAssign,
        ):
            if (
                isinstance(
                    dugum.target,
                    ast.Name,
                )
                and dugum.target.id == "app"
            ):
                adaylar.append(
                    dugum
                )

    if len(adaylar) != 1:
        raise RuntimeError(
            "Modül seviyesinde tam bir app ataması "
            "bulunamadı. Sayı: "
            f"{len(adaylar)}"
        )

    return adaylar[0]


def app_routerlarini_ekle(
    kaynak: str,
) -> str:
    sıkı = bosluksuz(
        kaynak
    )

    ui_var = (
        "app.include_router(syk_ui_router)"
        in sıkı
    )

    finans_var = (
        "app.include_router(finans_router)"
        in sıkı
    )

    if ui_var and finans_var:
        return kaynak

    agac = ayrıştır(
        kaynak
    )

    app_atamasi = app_atamasini_bul(
        agac
    )

    ekleme_indeksi = (
        app_atamasi.end_lineno
        or app_atamasi.lineno
    )

    bloklar = []

    if not ui_var:
        bloklar.append(
            UI_KAYDI
        )

    if not finans_var:
        bloklar.append(
            FINANS_KAYDI
        )

    satirlar = kaynak.splitlines(
        keepends=True
    )

    blok = (
        "\n"
        + "\n\n".join(
            bloklar
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

    ayrıştır(
        sonuc
    )

    return sonuc


metin = eksik_importlari_ekle(
    metin
)

metin = app_routerlarini_ekle(
    metin
)

sıkı = bosluksuz(
    metin
)

kontroller = {
    "ui_import": sıkı.count(
        "from.syk_ui_runtime.api_routes"
        "importrouterassyk_ui_router"
    ),
    "finans_import": sıkı.count(
        "from.syk_ui_runtime."
        "syfinans_runtime_routes"
        "importfinans_router"
    ),
    "ui_router": sıkı.count(
        "app.include_router(syk_ui_router)"
    ),
    "finans_router": sıkı.count(
        "app.include_router(finans_router)"
    ),
}

for ad, sayı in kontroller.items():
    if sayı != 1:
        raise RuntimeError(
            f"{ad} kayıt sayısı hatalı: {sayı}"
        )

if (
    "app.include_router(app)"
    in sıkı
    or "syk_ui_router.include_router("
    "syk_ui_router)"
    in sıkı
    or "finans_router.include_router("
    "finans_router)"
    in sıkı
):
    raise RuntimeError(
        "Kendi kendisini bağlayan router bulundu."
    )

HEDEF.write_text(
    metin,
    encoding="utf-8",
)

ayrıştır(
    HEDEF.read_text(
        encoding="utf-8"
    )
)

print(
    "GERCEK_APP_ROUTER_ENTEGRASYONU_OK"
)

print(
    "UI_IMPORT_SAYISI",
    kontroller["ui_import"],
)

print(
    "FINANS_IMPORT_SAYISI",
    kontroller["finans_import"],
)

print(
    "UI_ROUTER_KAYDI",
    kontroller["ui_router"],
)

print(
    "FINANS_ROUTER_KAYDI",
    kontroller["finans_router"],
)