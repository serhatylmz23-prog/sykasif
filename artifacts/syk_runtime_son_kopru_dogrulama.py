from __future__ import annotations

from fastapi.testclient import TestClient

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

yollar = tuple(
    route.path
    for route in app.routes
    if getattr(
        route,
        "path",
        None,
    )
)

eksikler: list[str] = []

for beklenen in beklenenler:
    eslesenler = sorted(
        yol
        for yol in yollar
        if (
            yol == beklenen
            or yol.startswith(
                beklenen.rstrip("/") + "/"
            )
        )
    )

    print(
        "HTTP_YOL",
        beklenen,
        "VAR" if eslesenler else "YOK",
    )

    for yol in eslesenler:
        print(
            "  ESLESEN",
            yol,
        )

    if not eslesenler:
        eksikler.append(
            beklenen
        )

if eksikler:
    print()
    print(
        "GERCEK_APP_ILGILI_YOLLARI"
    )

    for yol in sorted(
        set(
            yol
            for yol in yollar
            if any(
                ifade in yol.casefold()
                for ifade in (
                    "syk-ui",
                    "jarmin",
                    "mobile",
                    "kasif",
                    "finans",
                )
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


# Aynı yolun iki kez kaydolmadığını doğrula.
yinelenenler = sorted(
    {
        yol
        for yol in yollar
        if yollar.count(
            yol
        ) > 1
        and any(
            ifade in yol.casefold()
            for ifade in (
                "jarmin",
                "mobile",
                "kasif",
                "finans",
            )
        )
    }
)

if yinelenenler:
    raise RuntimeError(
        "Yinelenen runtime yolları: "
        + ", ".join(
            yinelenenler
        )
    )


istemci = TestClient(
    app
)

finans_yaniti = istemci.get(
    "/syfinans/runtime"
)

if finans_yaniti.status_code != 200:
    raise RuntimeError(
        "SyFinans runtime HTTP yanıtı başarısız: "
        f"{finans_yaniti.status_code}"
    )

finans_verisi = (
    finans_yaniti.json()
)

if finans_verisi.get(
    "modul"
) != "SyFinansOtağı":
    raise RuntimeError(
        "SyFinans runtime modül kimliği hatalı."
    )


print()
print(
    "SYFINANS_RUNTIME_HTTP",
    finans_yaniti.status_code,
)

print(
    "TOPLAM_APP_YOLU",
    len(
        yollar
    ),
)

print(
    "YINELENEN_ILGILI_YOL",
    len(
        yinelenenler
    ),
)

print(
    "YEDI_HTTP_YOLU_DOGRULANDI"
)