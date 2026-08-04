from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


RUNTIME = Path(
    "src/syk_simulasyon/"
    "syk_ui_runtime"
)

HEDEF = RUNTIME / "api_routes.py"

ISTENEN_PREFIXLER = (
    "/mobile-control",
    "/mobile-runtime",
    "/mobile-offline",
    "/mobile-sensors",
)

# Jarmin ve Kaşif ikon router'ları prefix yerine
# dosya ve içerik işaretleriyle ayrıca aranır.
EK_ISARETLER = (
    "jarmin",
    "kasif_icon",
    "kasif-icon",
    "kasif_icons",
)


@dataclass(frozen=True, slots=True)
class RouterBilgisi:
    dosya: Path
    nesne: str
    prefix: str | None


def ifade_adi(
    dugum: ast.AST,
) -> str:
    if isinstance(
        dugum,
        ast.Name,
    ):
        return dugum.id

    if isinstance(
        dugum,
        ast.Attribute,
    ):
        onceki = ifade_adi(
            dugum.value
        )

        return (
            f"{onceki}.{dugum.attr}"
            if onceki
            else dugum.attr
        )

    return ""


def sabit(
    dugum: ast.AST,
):
    try:
        return ast.literal_eval(
            dugum
        )
    except Exception:
        return None


def router_bilgisi(
    yol: Path,
) -> tuple[
    RouterBilgisi,
    ...
]:
    metin = yol.read_text(
        encoding="utf-8",
        errors="replace",
    )

    try:
        agac = ast.parse(
            metin,
            filename=str(yol),
        )
    except SyntaxError:
        return ()

    bulunanlar: list[
        RouterBilgisi
    ] = []

    for dugum in agac.body:
        if not isinstance(
            dugum,
            ast.Assign,
        ):
            continue

        if not isinstance(
            dugum.value,
            ast.Call,
        ):
            continue

        cagri = ifade_adi(
            dugum.value.func
        )

        if not cagri.endswith(
            "APIRouter"
        ):
            continue

        prefix = None

        for anahtar in (
            dugum.value.keywords
        ):
            if anahtar.arg == "prefix":
                deger = sabit(
                    anahtar.value
                )

                if deger is not None:
                    prefix = str(
                        deger
                    )

        for hedef in dugum.targets:
            nesne = ifade_adi(
                hedef
            )

            if nesne:
                bulunanlar.append(
                    RouterBilgisi(
                        dosya=yol,
                        nesne=nesne,
                        prefix=prefix,
                    )
                )

    return tuple(
        bulunanlar
    )


tum_routerlar: list[
    RouterBilgisi
] = []

for yol in sorted(
    RUNTIME.glob("*.py")
):
    if yol.name == "api_routes.py":
        continue

    tum_routerlar.extend(
        router_bilgisi(
            yol
        )
    )


secilenler: list[
    RouterBilgisi
] = []

for bilgi in tum_routerlar:
    metin = bilgi.dosya.read_text(
        encoding="utf-8",
        errors="replace",
    ).casefold()

    prefix_eslesmesi = (
        bilgi.prefix
        in ISTENEN_PREFIXLER
    )

    ek_eslesme = any(
        isaret in (
            bilgi.dosya.stem.casefold()
            + "\n"
            + metin
        )
        for isaret in EK_ISARETLER
    )

    if prefix_eslesmesi or ek_eslesme:
        if bilgi not in secilenler:
            secilenler.append(
                bilgi
            )


if not secilenler:
    raise RuntimeError(
        "Bağlanacak runtime router bulunamadı."
    )


metin = HEDEF.read_text(
    encoding="utf-8"
)

# Önce mevcut dosyanın sağlam olduğunu doğrula.
agac = ast.parse(
    metin,
    filename=str(HEDEF),
)


# -----------------------------------------------
# MODÜL SEVİYESİ IMPORT EKLEME
# -----------------------------------------------

import_bloklari: list[str] = []

for bilgi in secilenler:
    modul = bilgi.dosya.stem

    imza = (
        f"from .{modul} import"
    )

    if imza in metin:
        continue

    import_bloklari.append(
        (
            f"from .{modul} import (\n"
            f"    {bilgi.nesne},\n"
            f")\n"
        )
    )


if import_bloklari:
    govde = list(
        agac.body
    )

    ekleme_satiri = 0

    if (
        govde
        and isinstance(
            govde[0],
            ast.Expr,
        )
        and isinstance(
            govde[0].value,
            ast.Constant,
        )
        and isinstance(
            govde[0].value.value,
            str,
        )
    ):
        ekleme_satiri = (
            govde[0].end_lineno
            or govde[0].lineno
        )

    for dugum in govde:
        if isinstance(
            dugum,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            ekleme_satiri = max(
                ekleme_satiri,
                dugum.end_lineno
                or dugum.lineno,
            )
            continue

        if ekleme_satiri > 0:
            break

    satirlar = metin.splitlines(
        keepends=True
    )

    satirlar.insert(
        ekleme_satiri,
        "".join(
            import_bloklari
        ),
    )

    metin = "".join(
        satirlar
    )


# Import ekleme sonrasında hemen doğrula.
ast.parse(
    metin,
    filename=str(HEDEF),
)


# -----------------------------------------------
# ROUTER INCLUDE KAYITLARI
# -----------------------------------------------

eklenen_routerlar: list[str] = []

for bilgi in secilenler:
    tek_satir = (
        f"router.include_router("
        f"{bilgi.nesne})"
    )

    cok_satir = (
        "router.include_router(\n"
        f"    {bilgi.nesne}\n"
        ")"
    )

    if (
        tek_satir in metin
        or cok_satir in metin
    ):
        continue

    metin = (
        metin.rstrip()
        + "\n\n"
        + "router.include_router(\n"
        + f"    {bilgi.nesne}\n"
        + ")\n"
    )

    eklenen_routerlar.append(
        bilgi.nesne
    )


# Son sözdizimi doğrulaması.
ast.parse(
    metin,
    filename=str(HEDEF),
)


# Her router yalnız bir kez bağlanmış olmalı.
for bilgi in secilenler:
    sayi = (
        metin.count(
            f"    {bilgi.nesne}\n"
            ")"
        )
        + metin.count(
            f"include_router({bilgi.nesne})"
        )
    )

    if sayi != 1:
        raise RuntimeError(
            f"{bilgi.nesne} router kayıt "
            f"sayısı beklenenden farklı: {sayi}"
        )


HEDEF.write_text(
    metin,
    encoding="utf-8",
)


# Diske yazılan gerçek dosyayı yeniden doğrula.
ast.parse(
    HEDEF.read_text(
        encoding="utf-8"
    ),
    filename=str(HEDEF),
)


print(
    "SYK_EKSIK_RUNTIME_ROUTERLARI_BAGLANDI"
)

for bilgi in secilenler:
    print(
        "ROUTER",
        bilgi.nesne,
        "DOSYA",
        bilgi.dosya.as_posix(),
        "PREFIX",
        bilgi.prefix,
    )

print(
    "YENI_ROUTER_KAYDI",
    len(
        eklenen_routerlar
    ),
)

print(
    "SYK_RUNTIME_ROUTER_PATCH_OK"
)
