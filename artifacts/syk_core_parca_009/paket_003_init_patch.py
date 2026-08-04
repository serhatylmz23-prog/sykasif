from pathlib import Path

dosya = Path(
    "src/syk_core/runtime_prototype/__init__.py"
)

icerik = dosya.read_text(
    encoding="utf-8-sig"
)

aktarim = '''from .canli_dogrulama import (
    CanliYolSonucu,
    PrototipCanliDogrulamaHatasi,
    PrototipCanliDogrulayici,
    json_istegi,
)
'''

if "from .canli_dogrulama import (" not in icerik:
    aciklama = (
        '"""SyKaşif birleşik prototip paketi."""'
    )

    if aciklama not in icerik:
        raise RuntimeError(
            "Paket açıklaması bulunamadı."
        )

    icerik = icerik.replace(
        aciklama,
        aciklama + "\n\n" + aktarim,
        1,
    )

adlar = (
    "CanliYolSonucu",
    "PrototipCanliDogrulamaHatasi",
    "PrototipCanliDogrulayici",
    "json_istegi",
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
    "PROTOTIP_CANLI_DOGRULAMA_INIT_KAYDI_TAMAMLANDI"
)
