from __future__ import annotations

from pathlib import Path

dosya = Path(
    "src/syk_core/runtime_field_link/__init__.py"
)

icerik = dosya.read_text(
    encoding="utf-8-sig"
)

aktarim = '''from .yonetici import (
    SahaCihazBaglantiBilgisi,
    SahaCihazYonetimHatasi,
    SahaCihazYoneticisi,
)
'''

if "from .yonetici import (" not in icerik:
    aciklama = (
        '"""SyKaşif saha bağlantısı paketi."""'
    )

    icerik = icerik.replace(
        aciklama,
        aciklama + "\n\n" + aktarim,
        1,
    )

adlar = (
    "SahaCihazBaglantiBilgisi",
    "SahaCihazYonetimHatasi",
    "SahaCihazYoneticisi",
)

for ad in adlar:
    satir = f'    "{ad}",'

    if satir in icerik:
        continue

    kapanis = icerik.rfind("\n]")

    if kapanis < 0:
        raise RuntimeError(
            "__all__ kapanışı bulunamadı."
        )

    icerik = (
        icerik[:kapanis]
        + "\n"
        + satir
        + icerik[kapanis:]
    )

dosya.write_text(
    icerik,
    encoding="utf-8",
)

print(
    "SAHA_CIHAZ_YONETICI_INIT_KAYDI_TAMAMLANDI"
)
