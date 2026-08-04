from __future__ import annotations

import ast
import re
from pathlib import Path


HEDEF = Path(
    "src/syk_simulasyon/"
    "runtime_ui_sunucusu.py"
)

metin = HEDEF.read_text(
    encoding="utf-8"
)


def dogrula(
    kaynak: str,
) -> ast.Module:
    return ast.parse(
        kaynak,
        filename=str(HEDEF),
    )


# Önce mevcut dosyanın sağlamlığını doğrula.
dogrula(
    metin
)


# Önceki denemelerde eklenen importlar temizlenir.
eski_import_desenleri = (
    (
        r"(?m)^from \.syk_ui_runtime\.api_routes "
        r"import router as syk_ui_router\s*\n?"
    ),
    (
        r"(?m)^from \.syk_ui_runtime\."
        r"syfinans_runtime_routes "
        r"import finans_router\s*\n?"
    ),
)

for desen in eski_import_desenleri:
    metin = re.sub(
        desen,
        "",
        metin,
    )


# Önceki denemelerde farklı kapsamda kalmış
# include_router blokları temizlenir.
eski_kayit_desenleri = (
    (
        r"(?ms)^[ \t]*app\.include_router\(\s*"
        r"syk_ui_router\s*\)\s*\n?"
    ),
    (
        r"(?ms)^[ \t]*app\.include_router\(\s*"
        r"finans_router\s*\)\s*\n?"
    ),
)

for desen in eski_kayit_desenleri:
    metin = re.sub(
        desen,
        "",
        metin,
    )


kopru_baslangici = (
    "# === SYK_RUNTIME_ROUTER_KOPRUSU_BASLANGIC ==="
)

kopru_bitisi = (
    "# === SYK_RUNTIME_ROUTER_KOPRUSU_BITIS ==="
)


# Önceki köprü varsa bütünüyle yenilenir.
if (
    kopru_baslangici in metin
    and kopru_bitisi in metin
):
    baslangic = metin.index(
        kopru_baslangici
    )

    bitis = (
        metin.index(
            kopru_bitisi,
            baslangic,
        )
        + len(
            kopru_bitisi
        )
    )

    metin = (
        metin[:baslangic].rstrip()
        + "\n"
        + metin[bitis:].lstrip()
    )


kopru = r'''
# === SYK_RUNTIME_ROUTER_KOPRUSU_BASLANGIC ===

def _syk_route_var_mi(
    uygulama,
    yol: str,
) -> bool:
    return any(
        getattr(
            route,
            "path",
            None,
        ) == yol
        or str(
            getattr(
                route,
                "path",
                "",
            )
        ).startswith(
            yol.rstrip("/") + "/"
        )
        for route in uygulama.routes
    )


def _syk_runtime_routerlarini_bagla(
    uygulama,
) -> None:
    from .syk_ui_runtime.api_routes import (
        router as syk_ui_router,
    )

    from .syk_ui_runtime.syfinans_runtime_routes import (
        finans_router,
    )

    if not _syk_route_var_mi(
        uygulama,
        "/api/syk-ui",
    ):
        uygulama.include_router(
            syk_ui_router
        )

    if not _syk_route_var_mi(
        uygulama,
        "/syfinans",
    ):
        uygulama.include_router(
            finans_router
        )


_syk_runtime_routerlarini_bagla(
    app
)

# === SYK_RUNTIME_ROUTER_KOPRUSU_BITIS ===
'''


# Köprü her zaman modülün sonunda bulunur.
metin = (
    metin.rstrip()
    + "\n\n"
    + kopru.strip()
    + "\n"
)


# Son kaynak sözdizimi doğrulaması.
dogrula(
    metin
)


if metin.count(
    kopru_baslangici
) != 1:
    raise RuntimeError(
        "Runtime köprü başlangıç sayısı hatalı."
    )

if metin.count(
    kopru_bitisi
) != 1:
    raise RuntimeError(
        "Runtime köprü bitiş sayısı hatalı."
    )

if metin.count(
    "_syk_runtime_routerlarini_bagla(\n"
    "    app\n"
    ")"
) != 1:
    raise RuntimeError(
        "Runtime köprü çağrı sayısı hatalı."
    )


HEDEF.write_text(
    metin,
    encoding="utf-8",
)


# Diske yazılan gerçek kaynak yeniden doğrulanır.
dogrula(
    HEDEF.read_text(
        encoding="utf-8"
    )
)


print(
    "SYK_RUNTIME_SON_KOPRU_PATCH_OK"
)

print(
    "KOPRU_BASLANGIC_SAYISI",
    metin.count(
        kopru_baslangici
    ),
)

print(
    "KOPRU_BITIS_SAYISI",
    metin.count(
        kopru_bitisi
    ),
)

print(
    "KOPRU_CAGRI_SAYISI",
    metin.count(
        "_syk_runtime_routerlarini_bagla(\n"
        "    app\n"
        ")"
    ),
)