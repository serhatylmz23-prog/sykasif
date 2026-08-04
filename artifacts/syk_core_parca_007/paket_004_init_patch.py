from __future__ import annotations

from pathlib import Path

path = Path(
    "src/syk_core/runtime_device_link/__init__.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

import_block = '''from .api import (
    CanlilikIstegi,
    CihazIletisimAgGecidi,
    KomutOlusturmaIstegi,
    OturumAcmaIstegi,
    cihaz_iletisim_ag_gecidini_bagla,
)
'''

if "from .api import (" not in text:
    marker = (
        '"""SyKaşif cihazlar arası '
        'bağlantı paketi."""'
    )

    if marker not in text:
        raise RuntimeError(
            "Paket açıklama satırı bulunamadı."
        )

    text = text.replace(
        marker,
        marker + "\n\n" + import_block,
        1,
    )

exports = (
    "CanlilikIstegi",
    "CihazIletisimAgGecidi",
    "KomutOlusturmaIstegi",
    "OturumAcmaIstegi",
    "cihaz_iletisim_ag_gecidini_bagla",
)

for name in exports:
    if f'    "{name}",' in text:
        continue

    kapanis = text.rfind("\n]")

    if kapanis < 0:
        raise RuntimeError(
            "__all__ kapanışı bulunamadı."
        )

    text = (
        text[:kapanis]
        + f'\n    "{name}",'
        + text[kapanis:]
    )

path.write_text(
    text,
    encoding="utf-8",
)

print(
    "CIHAZ_ILETISIM_API_INIT_KAYDI_TAMAMLANDI"
)
