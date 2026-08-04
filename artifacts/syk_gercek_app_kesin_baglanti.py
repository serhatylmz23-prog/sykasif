from __future__ import annotations

import ast
import re
from pathlib import Path


HEDEF = Path(
    "src/syk_simulasyon/"
    "runtime_ui_sunucusu.py"
)

BASLANGIC = (
    "# === SYK_GERCEK_APP_KESIN_BAGLANTI_BASLANGIC ==="
)

BITIS = (
    "# === SYK_GERCEK_APP_KESIN_BAGLANTI_BITIS ==="
)


def parse(kaynak: str) -> ast.Module:
    return ast.parse(
        kaynak,
        filename=str(HEDEF),
    )


metin = HEDEF.read_text(
    encoding="utf-8"
)

agac = parse(metin)


# Önceki köprü bloklarını kaldır.
isaret_ciftleri = (
    (
        "# === SYK_RUNTIME_ROUTER_KOPRUSU_BASLANGIC ===",
        "# === SYK_RUNTIME_ROUTER_KOPRUSU_BITIS ===",
    ),
    (
        "# === SYK_KESIN_ROUTER_KOPRUSU_BASLANGIC ===",
        "# === SYK_KESIN_ROUTER_KOPRUSU_BITIS ===",
    ),
    (
        BASLANGIC,
        BITIS,
    ),
)

for baslangic, bitis in isaret_ciftleri:
    while (
        baslangic in metin
        and bitis in metin
    ):
        ilk = metin.index(
            baslangic
        )

        son = (
            metin.index(
                bitis,
                ilk,
            )
            + len(bitis)
        )

        metin = (
            metin[:ilk].rstrip()
            + "\n\n"
            + metin[son:].lstrip()
        )


# Önceki doğrudan eklemeleri temizle.
desenler = (
    (
        r"(?m)^from \.syk_ui_runtime\.api_routes "
        r"import router as syk_ui_router\s*\n?"
    ),
    (
        r"(?m)^from \.syk_ui_runtime\."
        r"syfinans_runtime_routes "
        r"import finans_router\s*\n?"
    ),
    (
        r"(?ms)^[ \t]*app\.include_router\(\s*"
        r"syk_ui_router\s*\)\s*\n?"
    ),
    (
        r"(?ms)^[ \t]*app\.include_router\(\s*"
        r"finans_router\s*\)\s*\n?"
    ),
)

for desen in desenler:
    metin = re.sub(
        desen,
        "",
        metin,
    )


agac = parse(metin)

app_atamalari = []

for dugum in agac.body:
    if isinstance(
        dugum,
        ast.Assign,
    ):
        if any(
            isinstance(hedef, ast.Name)
            and hedef.id == "app"
            for hedef in dugum.targets
        ):
            app_atamalari.append(
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
            app_atamalari.append(
                dugum
            )


if len(app_atamalari) != 1:
    raise RuntimeError(
        "Tek app ataması bulunamadı. "
        f"Sayı: {len(app_atamalari)}"
    )


app_atamasi = app_atamalari[0]

ekleme_indeksi = (
    app_atamasi.end_lineno
    or app_atamasi.lineno
)


blok = '''
# === SYK_GERCEK_APP_KESIN_BAGLANTI_BASLANGIC ===

from syk_simulasyon.syk_ui_runtime.api_routes import (
    router as syk_ui_router,
)

from syk_simulasyon.syk_ui_runtime.syfinans_runtime_routes import (
    finans_router,
)


def _syk_uygulama_yolu_var(
    yol: str,
) -> bool:
    return any(
        str(
            getattr(
                kayit,
                "path",
                "",
            )
        ) == yol
        or str(
            getattr(
                kayit,
                "path",
                "",
            )
        ).startswith(
            yol.rstrip("/") + "/"
        )
        for kayit in app.routes
    )


if not _syk_uygulama_yolu_var(
    "/api/syk-ui/mobile-runtime"
):
    app.include_router(
        syk_ui_router
    )


if not _syk_uygulama_yolu_var(
    "/syfinans/runtime"
):
    app.include_router(
        finans_router
    )

# === SYK_GERCEK_APP_KESIN_BAGLANTI_BITIS ===
'''


satirlar = metin.splitlines(
    keepends=True
)

satirlar.insert(
    ekleme_indeksi,
    "\n"
    + blok.strip()
    + "\n\n",
)

sonuc = "".join(
    satirlar
)

parse(sonuc)


if sonuc.count(BASLANGIC) != 1:
    raise RuntimeError(
        "Bağlantı başlangıç sayısı hatalı."
    )

if sonuc.count(BITIS) != 1:
    raise RuntimeError(
        "Bağlantı bitiş sayısı hatalı."
    )


HEDEF.write_text(
    sonuc,
    encoding="utf-8",
)

parse(
    HEDEF.read_text(
        encoding="utf-8"
    )
)


print(
    "SYK_GERCEK_APP_KESIN_BAGLANTI_OK"
)

print(
    "APP_ATAMA_SATIRI",
    app_atamasi.lineno,
)

print(
    "EKLEME_SATIRI",
    ekleme_indeksi + 1,
)

print(
    "BAGLANTI_BLOKU",
    1,
)