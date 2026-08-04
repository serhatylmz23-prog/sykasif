from __future__ import annotations

from pathlib import Path
import re

from playwright.sync_api import (
    sync_playwright,
)


dosya = Path(
    "src/syk_simulasyon/syk_ui_runtime/"
    "static/js/mobile_sensor_runtime.js"
)

kaynak = dosya.read_text(
    encoding="utf-8",
)

with sync_playwright() as playwright:
    tarayici = playwright.chromium.launch(
        headless=True,
    )

    sayfa = tarayici.new_page()

    sonuc = sayfa.evaluate(
        """
        kaynak => {
            try {
                new Function(
                    kaynak
                    + "\\n//# sourceURL="
                    + "mobile_sensor_runtime.js"
                );

                return {
                    basarili: true,
                    mesaj: null,
                    yigin: null,
                };
            }
            catch (hata) {
                return {
                    basarili: false,
                    mesaj: String(
                        hata.message
                    ),
                    yigin: String(
                        hata.stack || ""
                    ),
                };
            }
        }
        """,
        kaynak,
    )

    tarayici.close()


print(
    "JAVASCRIPT_YAZIM_SONUCU",
    sonuc,
)

if sonuc["basarili"]:
    print(
        "MOBIL_SENSOR_JAVASCRIPT_YAZIMI_OK"
    )
    raise SystemExit(0)


yigin = sonuc.get(
    "yigin"
) or ""

eslesmeler = re.findall(
    r"mobile_sensor_runtime\\.js:"
    r"(\\d+)(?::(\\d+))?",
    yigin,
)

if not eslesmeler:
    print(
        "HATA_SATIRI_YIGINDA_BULUNAMADI"
    )

    # Kesin satırı bulmak için dosyayı
    # parça parça derleyerek ilk bozulan
    # bölgeyi tespit et.
    satirlar = kaynak.splitlines()

    alt = 1
    ust = len(satirlar)

    while alt < ust:
        orta = (
            alt + ust
        ) // 2

        parca = "\n".join(
            satirlar[:orta]
        )

        with sync_playwright() as playwright:
            tarayici = (
                playwright.chromium.launch(
                    headless=True,
                )
            )

            sayfa = tarayici.new_page()

            deneme = sayfa.evaluate(
                """
                kaynak => {
                    try {
                        new Function(kaynak);
                        return true;
                    }
                    catch {
                        return false;
                    }
                }
                """,
                parca,
            )

            tarayici.close()

        if deneme:
            alt = orta + 1
        else:
            ust = orta

    hata_satiri = alt
else:
    hata_satiri = int(
        eslesmeler[-1][0]
    )


satirlar = kaynak.splitlines()

baslangic = max(
    1,
    hata_satiri - 12,
)

bitis = min(
    len(satirlar),
    hata_satiri + 12,
)

print()
print(
    f"=== HATA ÇEVRESİ: "
    f"SATIR {hata_satiri} ==="
)

for numara in range(
    baslangic,
    bitis + 1,
):
    isaret = (
        ">>>"
        if numara == hata_satiri
        else "   "
    )

    print(
        f"{isaret} "
        f"{numara:04d}: "
        f"{satirlar[numara - 1]}"
    )

raise SystemExit(1)
