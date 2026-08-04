from pathlib import Path

dosya = Path(
    "src/syk_core/runtime_hardware_validation/__init__.py"
)

icerik = dosya.read_text(
    encoding="utf-8-sig"
)

aktarim = '''from .sistem_denetimi import (
    AgArayuzuBilgisi,
    AgNoktasiSonucu,
    DenetimDurumu,
    DenetimTuru,
    GercekSistemDenetleyicisi,
    KomutSonucu,
    SeriBaglantiBilgisi,
    SistemDenetimHatasi,
    SistemDenetimSonucu,
    UsbCihazBilgisi,
    ag_noktasi_denetle,
    komut_calistir,
)
'''

if "from .sistem_denetimi import (" not in icerik:
    aciklama = (
        '"""SyKaşif gerçek donanım doğrulama paketi."""'
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
    "AgArayuzuBilgisi",
    "AgNoktasiSonucu",
    "DenetimDurumu",
    "DenetimTuru",
    "GercekSistemDenetleyicisi",
    "KomutSonucu",
    "SeriBaglantiBilgisi",
    "SistemDenetimHatasi",
    "SistemDenetimSonucu",
    "UsbCihazBilgisi",
    "ag_noktasi_denetle",
    "komut_calistir",
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
    "SISTEM_DENETIMI_INIT_KAYDI_TAMAMLANDI"
)
