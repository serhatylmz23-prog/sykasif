from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from starlette.routing import Mount

from syk_simulasyon.runtime_ui_sunucusu import app


RAPOR = Path(
    "artifacts/"
    "SYK_IC_ICE_YONLENDIRICI_HTTP_RAPORU.txt"
)


BEKLENENLER = (
    "/api/syk-ui/jarmin/integration",
    "/api/syk-ui/mobile-runtime",
    "/api/syk-ui/mobile-sensors",
    "/api/syk-ui/mobile-offline",
    "/api/syk-ui/mobile-control",
    "/api/syk-ui/kasif-icons",
    "/syfinans/runtime",
)


def birlestir(
    kok: str,
    yol: str,
) -> str:
    if not kok:
        return yol or "/"

    if yol in {
        "",
        "/",
    }:
        return kok or "/"

    return (
        kok.rstrip("/")
        + "/"
        + yol.lstrip("/")
    )


def tum_yollari_getir(
    uygulama: Any,
    kok: str = "",
) -> list[
    dict[str, Any]
]:
    bulunanlar: list[
        dict[str, Any]
    ] = []

    for kayit in getattr(
        uygulama,
        "routes",
        (),
    ):
        yol = str(
            getattr(
                kayit,
                "path",
                "",
            )
        )

        tam_yol = birlestir(
            kok,
            yol,
        )

        bulunanlar.append(
            {
                "yol": tam_yol,
                "tur": (
                    type(kayit).__name__
                ),
                "yontemler": sorted(
                    getattr(
                        kayit,
                        "methods",
                        (),
                    )
                    or ()
                ),
                "ad": getattr(
                    kayit,
                    "name",
                    None,
                ),
            }
        )

        if isinstance(
            kayit,
            Mount,
        ):
            alt_uygulama = getattr(
                kayit,
                "app",
                None,
            )

            if alt_uygulama is not None:
                bulunanlar.extend(
                    tum_yollari_getir(
                        alt_uygulama,
                        tam_yol,
                    )
                )

    return bulunanlar


istemci = TestClient(
    app,
    raise_server_exceptions=False,
)

tum_yollar = tum_yollari_getir(
    app
)

yol_kumesi = {
    kayit["yol"]
    for kayit in tum_yollar
}

satirlar = [
    (
        "SYK İÇ İÇE YÖNLENDİRİCİ "
        "VE HTTP DOĞRULAMASI"
    ),
    "",
    (
        "ÜST DÜZEY YOL SAYISI: "
        f"{len(app.routes)}"
    ),
    (
        "İÇ İÇE TOPLAM YOL SAYISI: "
        f"{len(tum_yollar)}"
    ),
    "",
    "BEKLENEN YOLLAR",
]

basarisizlar = []

for beklenen in BEKLENENLER:
    eslesenler = sorted(
        yol
        for yol in yol_kumesi
        if (
            yol == beklenen
            or yol.startswith(
                beklenen.rstrip("/")
                + "/"
            )
        )
    )

    yanit = istemci.get(
        beklenen
    )

    # 405: Yol var, kullanılan HTTP yöntemi farklı.
    http_var = (
        yanit.status_code
        != 404
    )

    zincirde_var = bool(
        eslesenler
    )

    durum = (
        "VAR"
        if (
            http_var
            or zincirde_var
        )
        else "YOK"
    )

    satirlar.append(
        (
            f"{beklenen} | "
            f"ZİNCİR={zincirde_var} | "
            f"HTTP={yanit.status_code} | "
            f"DURUM={durum}"
        )
    )

    print(
        "YOL",
        beklenen,
        durum,
        "ZINCIR",
        zincirde_var,
        "HTTP",
        yanit.status_code,
    )

    for eslesen in eslesenler:
        print(
            "  ESLESEN",
            eslesen,
        )

    if durum == "YOK":
        basarisizlar.append(
            beklenen
        )


satirlar.extend(
    [
        "",
        "İLGİLİ İÇ İÇE YOLLAR",
    ]
)

for kayit in sorted(
    tum_yollar,
    key=lambda oge: (
        oge["yol"],
        oge["tur"],
    ),
):
    if any(
        ifade in kayit[
            "yol"
        ].casefold()
        for ifade in (
            "syk-ui",
            "mobile",
            "jarmin",
            "kasif",
            "finans",
        )
    ):
        satirlar.append(
            (
                f"{kayit['tur']} | "
                f"{kayit['yol']} | "
                f"{','.join(kayit['yontemler'])}"
            )
        )


RAPOR.write_text(
    "\n".join(
        satirlar
    )
    + "\n",
    encoding="utf-8",
)


if basarisizlar:
    raise RuntimeError(
        "Gerçekte bulunamayan yollar: "
        + ", ".join(
            basarisizlar
        )
    )


print()
print(
    "UST_DUZEY_YOL",
    len(
        app.routes
    ),
)

print(
    "IC_ICE_TOPLAM_YOL",
    len(
        tum_yollar
    ),
)

print(
    "YEDI_YOL_HTTP_DOGRULANDI"
)

print(
    "RAPOR",
    RAPOR,
)