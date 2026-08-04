from pathlib import Path
import ast


sozlesme_yolu = Path(
    "src/syk_finans_otagi/"
    "gercek_kaynak_sozlesmeleri.py"
)

tcmb_yolu = Path(
    "src/syk_finans_otagi/"
    "tcmb_guvenli_calisma.py"
)


# =========================================================
# FİNANSAL YUVARLAMA
# =========================================================

metin = sozlesme_yolu.read_text(
    encoding="utf-8",
)

eski_import = (
    "from decimal import Decimal\n"
)

yeni_import = (
    "from decimal import Decimal, ROUND_HALF_UP\n"
)

if eski_import in metin:
    metin = metin.replace(
        eski_import,
        yeni_import,
        1,
    )
elif (
    "from decimal import Decimal, ROUND_HALF_UP"
    not in metin
):
    raise RuntimeError(
        "Decimal içe aktarma satırı bulunamadı."
    )


eski_ondalik = '''    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001")
    )
'''

yeni_ondalik = '''    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )
'''

if eski_ondalik in metin:
    metin = metin.replace(
        eski_ondalik,
        yeni_ondalik,
        1,
    )
elif (
    "rounding=ROUND_HALF_UP"
    not in metin
):
    raise RuntimeError(
        "Ortak ondalık dönüştürme bölümü bulunamadı."
    )

sozlesme_yolu.write_text(
    metin,
    encoding="utf-8",
)

ast.parse(
    sozlesme_yolu.read_text(
        encoding="utf-8",
    )
)


# =========================================================
# KULLANICI AÇIKLAMASI
# =========================================================

metin = tcmb_yolu.read_text(
    encoding="utf-8",
)

eski_aciklama = '''                kullanici_aciklamasi=(
                    "TCMB verisi canlı "
                    "bağlantıdan alındı. "
                    "Gösterge kuru niteliğindedir."
                ),
'''

yeni_aciklama = '''                kullanici_aciklamasi=(
                    "TCMB verisi canlı "
                    "bağlantıdan alındı; "
                    "gösterge kuru niteliğindedir."
                ),
'''

if eski_aciklama in metin:
    metin = metin.replace(
        eski_aciklama,
        yeni_aciklama,
        1,
    )
elif (
    '"gösterge kuru niteliğindedir."'
    not in metin
):
    raise RuntimeError(
        "TCMB kullanıcı açıklaması bulunamadı."
    )

tcmb_yolu.write_text(
    metin,
    encoding="utf-8",
)

ast.parse(
    tcmb_yolu.read_text(
        encoding="utf-8",
    )
)

print(
    "TCMB_FINANSAL_YUVARLAMA_DUZELTILDI"
)

print(
    "TCMB_KULLANICI_ACIKLAMASI_DUZELTILDI"
)
