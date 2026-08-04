from pathlib import Path

dosya = Path(
    "src/syk_core/runtime_hardware_validation/__init__.py"
)

icerik = dosya.read_text(
    encoding="utf-8-sig"
)

aktarim = '''from .komut_araci import (
    DonanimDenetimAraci,
    DonanimDenetimAraciHatasi,
    DonanimDenetimSecenekleri,
    ag_noktasi_ayristir,
    main as donanim_denetim_main,
)
'''

if "from .komut_araci import (" not in icerik:
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
    "DonanimDenetimAraci",
    "DonanimDenetimAraciHatasi",
    "DonanimDenetimSecenekleri",
    "ag_noktasi_ayristir",
    "donanim_denetim_main",
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
    "DONANIM_DENETIM_KOMUT_ARACI_INIT_KAYDI_TAMAMLANDI"
)
