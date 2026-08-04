from pathlib import Path

dosya = Path(
    "src/syk_core/runtime_field_link/__init__.py"
)

icerik = dosya.read_text(
    encoding="utf-8-sig"
)

aktarim = '''from .terminal_entegrasyonu import (
    SahaTerminalEntegrasyonHatasi,
    SahaTerminalKoprusu,
    terminale_saha_cihazlarini_bagla,
)
'''

if (
    "from .terminal_entegrasyonu import ("
    not in icerik
):
    aciklama = (
        '"""SyKaşif saha bağlantısı paketi."""'
    )

    if aciklama not in icerik:
        raise RuntimeError(
            "Paket açıklama satırı bulunamadı."
        )

    icerik = icerik.replace(
        aciklama,
        aciklama + "\n\n" + aktarim,
        1,
    )

adlar = (
    "SahaTerminalEntegrasyonHatasi",
    "SahaTerminalKoprusu",
    "terminale_saha_cihazlarini_bagla",
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
    "SAHA_TERMINAL_ENTEGRASYONU_INIT_KAYDI_TAMAMLANDI"
)
