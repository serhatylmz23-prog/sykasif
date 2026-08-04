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

    print(
        "HTTP_YOL",
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
        yol
        for yol in yollar
        if any(
            ifade in yol.casefold()
            for ifade in (
                "jarmin",
                "mobile",
                "kasif",
                "finans",
                "syk-ui",
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

istemci = TestClient(
    app
)

runtime_yaniti = istemci.get(
    "/syfinans/runtime"
)

if runtime_yaniti.status_code != 200:
    raise RuntimeError(
        "SyFinans runtime HTTP yanıtı başarısız: "
        f"{runtime_yaniti.status_code}"
    )

runtime_verisi = runtime_yaniti.json()

if runtime_verisi.get(
    "modul"
) != "SyFinansOtağı":
    raise RuntimeError(
        "SyFinans runtime modül kimliği hatalı."
    )

print()
print(
    "SYFINANS_RUNTIME_HTTP",
    runtime_yaniti.status_code,
)

print(
    "TOPLAM_APP_YOLU",
    len(yollar),
)

print(
    "YEDI_HTTP_YOLU_DOGRULANDI"
)