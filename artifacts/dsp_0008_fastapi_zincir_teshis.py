from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


kaynak = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

rapor: list[str] = []


def yaz(*parcalar: Any) -> None:
    metin = " ".join(
        str(parca)
        for parca in parcalar
    )

    print(metin)
    rapor.append(metin)


try:
    yaz("=" * 70)
    yaz("DOSYA:", kaynak)
    yaz("=" * 70)

    metin = kaynak.read_text(
        encoding="utf-8-sig"
    )

    agac = ast.parse(
        metin,
        filename=str(kaynak),
    )

    for dugum in agac.body:
        if isinstance(
            dugum,
            ast.ImportFrom,
        ):
            modul = dugum.module or ""

            if any(
                ifade in modul
                for ifade in (
                    "runtime",
                    "terminal",
                    "finans",
                )
            ):
                yaz(
                    "IMPORT",
                    dugum.lineno,
                    ast.unparse(dugum),
                )

        if isinstance(
            dugum,
            ast.ClassDef,
        ) and dugum.name == "RuntimeFastApiSunucusu":
            for uye in dugum.body:
                if (
                    isinstance(
                        uye,
                        ast.FunctionDef,
                    )
                    and uye.name == "olustur"
                ):
                    yaz(
                        "METOT",
                        uye.name,
                        "SATIR",
                        uye.lineno,
                    )

                    for alt in ast.walk(uye):
                        if not isinstance(
                            alt,
                            ast.Call,
                        ):
                            continue

                        if isinstance(
                            alt.func,
                            ast.Name,
                        ) and alt.func.id == "FastAPI":
                            yaz(
                                "FASTAPI_CALL",
                                alt.lineno,
                            )

                        if isinstance(
                            alt.func,
                            ast.Attribute,
                        ) and alt.func.attr == "include_router":
                            yaz(
                                "INCLUDE_ROUTER",
                                alt.lineno,
                                ast.unparse(alt),
                            )

        if (
            isinstance(
                dugum,
                ast.FunctionDef,
            )
            and dugum.name == "uygulama_olustur"
        ):
            yaz(
                "FONKSIYON",
                dugum.name,
                "SATIR",
                dugum.lineno,
            )

            for alt in ast.walk(dugum):
                if not isinstance(
                    alt,
                    ast.Call,
                ):
                    continue

                if isinstance(
                    alt.func,
                    ast.Name,
                ) and alt.func.id == "RuntimeFastApiSunucusu":
                    yaz(
                        "SUNUCU_CALL",
                        alt.lineno,
                        ast.unparse(alt),
                    )

                if isinstance(
                    alt.func,
                    ast.Attribute,
                ) and alt.func.attr == "olustur":
                    yaz(
                        "OLUSTUR_CALL",
                        alt.lineno,
                        ast.unparse(alt),
                    )

                if isinstance(
                    alt.func,
                    ast.Attribute,
                ) and alt.func.attr == "include_router":
                    yaz(
                        "INCLUDE_ROUTER",
                        alt.lineno,
                        ast.unparse(alt),
                    )

    from syk_simulasyon.runtime_fastapi_sunucusu import (
        uygulama_olustur,
    )

    yaz()
    yaz("=" * 70)
    yaz("GERCEK UYGULAMA YOLLARI")
    yaz("=" * 70)

    uygulama = uygulama_olustur(
        hesap_deposu_etkin=False
    )

    yollar = [
        getattr(
            route,
            "path",
            "",
        )
        for route in uygulama.routes
    ]

    for yol in yollar:
        if yol:
            yaz(
                "APP_ROUTE",
                yol,
            )

    for hedef in (
        "/api/syk-ui/terminal/state",
        "/syfinans/runtime",
    ):
        yaz(
            "HEDEF",
            hedef,
            "SAYI",
            yollar.count(hedef),
        )

    yaz()
    yaz(
        "SYK_DSP_0008_FASTAPI_ZINCIR_TESHIS_OK"
    )

finally:
    Path(
        "artifacts/SYK_DSP_0008_FASTAPI_BASLANGIC_ZINCIRI.txt"
    ).write_text(
        "\n".join(rapor) + "\n",
        encoding="utf-8",
    )