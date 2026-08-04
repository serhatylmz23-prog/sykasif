from __future__ import annotations

from syk_simulasyon.runtime_ui_sunucusu import app


beklenenler = (
    "/api/syk-ui/jarmin/integration",
    "/api/syk-ui/mobile-runtime",
    "/api/syk-ui/mobile-sensors",
    "/api/syk-ui/mobile-offline",
    "/api/syk-ui/mobile-control",
    "/api/syk-ui/kasif-icons",
    "/syfinans/runtime",
)

yollar = {
    route.path
    for route in app.routes
    if getattr(
        route,
        "path",
        None,
    )
}

eksikler: list[str] = []

for beklenen in beklenenler:
    eslesenler = sorted(
        yol
        for yol in yollar
        if (
            yol == beklenen
            or yol.startswith(
                beklenen + "/"
            )
        )
    )

    bulundu = bool(
        eslesenler
    )

    print(
        "HTTP_YOL",
        beklenen,
        "VAR" if bulundu else "YOK",
    )

    for yol in eslesenler:
        print(
            "  ESLESEN",
            yol,
        )

    if not bulundu:
        eksikler.append(
            beklenen
        )

if eksikler:
    print()
    print(
        "KAYITLI_ILGILI_YOLLAR"
    )

    for yol in sorted(
        yol
        for yol in yollar
        if any(
            ifade in yol.casefold()
            for ifade in (
                "jarmin",
                "mobile",
                "kasif",
                "finans",
            )
        )
    ):
        print(
            " ",
            yol,
        )

    raise RuntimeError(
        "Eksik HTTP yolları: "
        + ", ".join(
            eksikler
        )
    )

print()
print(
    "YEDI_HTTP_YOLU_DOGRULANDI"
)