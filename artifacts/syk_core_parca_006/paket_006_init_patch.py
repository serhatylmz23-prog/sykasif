from __future__ import annotations

from pathlib import Path

path = Path(
    "src/syk_core/runtime_terminal/__init__.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

import_block = '''from .uygulama import (
    GuvenliSistemIsletmeni,
    SyKasifTerminalUygulamasi,
    YerelUygulamaIsletmeni,
    terminal_uygulamasi_olustur,
)
from .uygulama_modelleri import (
    CalismaKipi,
    TerminalUygulamasiAyarlari,
    TerminalUygulamasiHatasi,
    YetkiliCihazAyari,
)
'''

if "from .uygulama import (" not in text:
    marker = '"""SyKaşif çalışma terminali."""'

    if marker not in text:
        raise RuntimeError(
            "Runtime terminal açıklama satırı bulunamadı."
        )

    text = text.replace(
        marker,
        marker + "\n\n" + import_block,
        1,
    )

exports = (
    "CalismaKipi",
    "GuvenliSistemIsletmeni",
    "SyKasifTerminalUygulamasi",
    "TerminalUygulamasiAyarlari",
    "TerminalUygulamasiHatasi",
    "YerelUygulamaIsletmeni",
    "YetkiliCihazAyari",
    "terminal_uygulamasi_olustur",
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
    "TERMINAL_UYGULAMASI_INIT_KAYDI_TAMAMLANDI"
)
