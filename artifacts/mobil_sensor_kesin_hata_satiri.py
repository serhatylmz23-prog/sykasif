from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


adres = os.getenv(
    "SYK_UI_TEST_URL",
    "http://127.0.0.1:8013/syk-ui-screen",
)

kaynak_yolu = Path(
    "src/syk_simulasyon/syk_ui_runtime/"
    "static/js/mobile_sensor_runtime.js"
)

satirlar = kaynak_yolu.read_text(
    encoding="utf-8",
).splitlines()

hatalar: list[dict] = []


with sync_playwright() as playwright:
    tarayici = playwright.chromium.launch(
        headless=True,
    )

    sayfa = tarayici.new_page()

    cdp = sayfa.context.new_cdp_session(
        sayfa
    )

    cdp.send(
        "Runtime.enable"
    )

    def hata_yakala(
        olay: dict,
    ) -> None:
        ayrinti = olay.get(
            "exceptionDetails",
            {},
        )

        adres_degeri = ayrinti.get(
            "url",
            "",
        )

        aciklama = ayrinti.get(
            "text",
            "",
        )

        istisna = ayrinti.get(
            "exception",
            {},
        )

        tam_aciklama = istisna.get(
            "description",
            aciklama,
        )

        hata = {
            "adres": adres_degeri,
            "satir": (
                int(
                    ayrinti.get(
                        "lineNumber",
                        0,
                    )
                )
                + 1
            ),
            "sutun": (
                int(
                    ayrinti.get(
                        "columnNumber",
                        0,
                    )
                )
                + 1
            ),
            "aciklama": tam_aciklama,
        }

        hatalar.append(
            hata
        )

    cdp.on(
        "Runtime.exceptionThrown",
        hata_yakala,
    )

    sayfa.goto(
        adres,
        wait_until="networkidle",
    )

    sayfa.wait_for_timeout(
        1000
    )

    tarayici.close()


uygun_hatalar = [
    hata
    for hata in hatalar
    if (
        "mobile_sensor_runtime.js"
        in hata["adres"]
        or "missing ) after argument list"
        in hata["aciklama"]
    )
]

if not uygun_hatalar:
    print(
        "MOBIL_SENSOR_HATASI_YAKALANAMADI"
    )

    print(
        "YAKALANAN_HATALAR",
        hatalar,
    )

    raise SystemExit(1)


hata = uygun_hatalar[0]
satir = hata["satir"]
sutun = hata["sutun"]

print(
    "MOBIL_SENSOR_KESIN_HATA",
    f"satir={satir}",
    f"sutun={sutun}",
)

print(
    "ACIKLAMA",
    hata["aciklama"],
)

baslangic = max(
    1,
    satir - 10,
)

bitis = min(
    len(satirlar),
    satir + 10,
)

print()
print(
    f"=== HATA ÇEVRESİ "
    f"SATIR {satir}, SÜTUN {sutun} ==="
)

for numara in range(
    baslangic,
    bitis + 1,
):
    isaret = (
        ">>>"
        if numara == satir
        else "   "
    )

    print(
        f"{isaret} "
        f"{numara:04d}: "
        f"{satirlar[numara - 1]}"
    )

print()
print(
    "MOBIL_SENSOR_KESIN_HATA_SATIRI_OK"
)
