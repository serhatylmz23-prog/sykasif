from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
)


url = os.getenv(
    "SYK_UI_TEST_URL",
    "http://127.0.0.1:8013/syk-ui-screen",
)

rapor: list[str] = []


def kaydet(
    satir: str,
) -> None:
    print(satir)
    rapor.append(satir)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True,
    )

    page = browser.new_page()

    page.on(
        "console",
        lambda mesaj: kaydet(
            "KONSOL "
            f"{mesaj.type}: "
            f"{mesaj.text}"
        ),
    )

    page.on(
        "pageerror",
        lambda hata: kaydet(
            "SAYFA_HATASI "
            f"{hata}"
        ),
    )

    page.on(
        "requestfailed",
        lambda istek: kaydet(
            "İSTEK_BAŞARISIZ "
            f"{istek.url} "
            f"{istek.failure}"
        ),
    )

    def yanit_kaydet(
        yanit,
    ) -> None:
        if (
            "mobile_sensor_runtime.js"
            in yanit.url
        ):
            kaydet(
                "MOBİL_SENSOR_YANITI "
                f"durum={yanit.status} "
                f"adres={yanit.url}"
            )

    page.on(
        "response",
        yanit_kaydet,
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    page.wait_for_timeout(
        1000
    )

    durum = page.evaluate(
        """
        () => ({
            mobilSensorTuru:
                typeof window
                    .SyKMobileSensors,

            kameraTuru:
                typeof window
                    .SyKMobileSensors
                    ?.startCamera,

            mikrofonTuru:
                typeof window
                    .SyKMobileSensors
                    ?.startMicrophone,

            konumTuru:
                typeof window
                    .SyKMobileSensors
                    ?.requestLocation,

            betikSayisi:
                Array.from(
                    document.scripts
                ).filter(
                    script =>
                        script.src.includes(
                            "mobile_sensor_runtime.js"
                        )
                ).length,

            betikAdresi:
                Array.from(
                    document.scripts
                ).find(
                    script =>
                        script.src.includes(
                            "mobile_sensor_runtime.js"
                        )
                )?.src || null,
        })
        """
    )

    kaydet(
        "MOBİL_SENSOR_DURUMU "
        f"{durum}"
    )

    browser.close()


rapor_yolu = Path(
    "artifacts/"
    "MOBIL_SENSOR_TARAYICI_HATA_RAPORU.txt"
)

rapor_yolu.write_text(
    "\n".join(rapor),
    encoding="utf-8",
)

print(
    "MOBİL_SENSOR_TARAYICI_İNCELEME_OK"
)
print(
    "RAPOR",
    rapor_yolu
)
