from pathlib import Path
import re


kok = Path(
    "src/syk_simulasyon/syk_ui_runtime/static"
)

dosyalar = [
    *kok.rglob("*.html"),
    *kok.rglob("*.js"),
]

desen = re.compile(
    r'<button'
    r'(?P<ozellikler>[^>]*'
    r'class=["\'][^"\']*'
    r'\bsyk-module-button\b'
    r'[^"\']*["\'][^>]*)'
    r'>\s*GPS\s*</button>',
    flags=re.IGNORECASE,
)

degisenler: list[str] = []

for yol in dosyalar:
    metin = yol.read_text(
        encoding="utf-8",
    )

    def degistir(
        eslesme: re.Match[str],
    ) -> str:
        ozellikler = eslesme.group(
            "ozellikler"
        )

        if "aria-label=" not in ozellikler:
            ozellikler += (
                ' aria-label="Konum bölümü"'
            )

        return (
            f"<button{ozellikler}>"
            "GPS"
            "</button>"
        )

    yeni_metin, adet = desen.subn(
        degistir,
        metin,
    )

    if adet:
        yol.write_text(
            yeni_metin,
            encoding="utf-8",
        )

        degisenler.append(
            f"{yol.as_posix()}:{adet}"
        )

if not degisenler:
    raise RuntimeError(
        "Ana GPS bölüm düğmesi bulunamadı."
    )

print("GPS_ERISILEBILIR_ADI_DUZELTILDI")

for kayit in degisenler:
    print(kayit)
