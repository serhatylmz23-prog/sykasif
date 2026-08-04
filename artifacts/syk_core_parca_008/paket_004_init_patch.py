from pathlib import Path

dosya = Path(
    "src/syk_core/runtime_field_link/__init__.py"
)

icerik = dosya.read_text(
    encoding="utf-8-sig"
)

aktarim = '''from .api import (
    EslestirmeBaslatmaIstegi,
    EslestirmeOnayIstegi,
    EslestirmeTamamlamaIstegi,
    SahaCihazAgGecidi,
    YenidenBaglanmaIstegi,
    saha_cihaz_ag_gecidini_bagla,
)
'''

if "from .api import (" not in icerik:
    aciklama = (
        '"""SyKaşif saha bağlantısı paketi."""'
    )

    icerik = icerik.replace(
        aciklama,
        aciklama + "\n\n" + aktarim,
        1,
    )

adlar = (
    "EslestirmeBaslatmaIstegi",
    "EslestirmeOnayIstegi",
    "EslestirmeTamamlamaIstegi",
    "SahaCihazAgGecidi",
    "YenidenBaglanmaIstegi",
    "saha_cihaz_ag_gecidini_bagla",
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

print("SAHA_CIHAZ_API_INIT_KAYDI_TAMAMLANDI")
