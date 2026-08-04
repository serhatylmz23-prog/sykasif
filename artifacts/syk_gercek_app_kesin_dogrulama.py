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
    str(route.path)
    for route in app.routes
    if getattr(
        route,
        "path",
        None,
    )
)

eksikler = []

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
        "YOL",
        beklenen,
        "VAR" if eslesenler else "YOK",
    )

    for eslesen in eslesenler:
        print(
            "  ESLESEN",
            eslesen,
        )

    if not eslesenler:
        eksikler.append(
            beklenen
        )


if eksikler:
    print()
    print(
        "MEVCUT_ILGILI_YOLLAR"
    )

    for yol in sorted(
        set(
            yol
            for yol in yollar
            if any(
                ifade in yol.casefold()
                for ifade in (
                    "syk-ui",
                    "mobile",
                    "jarmin",
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
        "Eksik yollar: "
        + ", ".join(
            eksikler
        )
    )


yinelenenler = sorted(
    {
        yol
        for yol in yollar
        if yollar.count(yol) > 1
        and any(
            ifade in yol.casefold()
            for ifade in (
                "mobile",
                "jarmin",
                "kasif",
                "finans",
            )
        )
    }
)

if yinelenenler:
    raise RuntimeError(
        "Yinelenen yollar: "
        + ", ".join(
            yinelenenler
        )
    )


istemci = TestClient(app)

finans = istemci.get(
    "/syfinans/runtime"
)

if finans.status_code != 200:
    raise RuntimeError(
        "SyFinans yanıtı başarısız: "
        f"{finans.status_code}"
    )


print()
print(
    "TOPLAM_UYGULAMA_YOLU",
    len(yollar),
)

print(
    "YINELENEN_YOL",
    len(yinelenenler),
)

print(
    "SYFINANS_HTTP",
    finans.status_code,
)

print(
    "YEDI_YOL_DOGRULANDI"
)