from pathlib import Path
import ast


path = Path(
    "src/syk_finans_otagi/"
    "kap_bildirim_bagdastiricisi.py"
)

text = path.read_text(
    encoding="utf-8",
)


old_import = '''import os
from pathlib import Path
'''

new_import = '''import os
from pathlib import Path
import unicodedata
'''

if old_import in text:
    text = text.replace(
        old_import,
        new_import,
        1,
    )
elif "import unicodedata" not in text:
    raise RuntimeError(
        "KAP içe aktarma bölümü bulunamadı."
    )


marker = "SYF_KAP_TURKCE_METIN_NORMALLESTIRME"

normalizer = '''
# SYF_KAP_TURKCE_METIN_NORMALLESTIRME
def _arama_metni(
    deger: str,
) -> str:
    metin = unicodedata.normalize(
        "NFKD",
        str(
            deger
        ).casefold(),
    )

    metin = "".join(
        karakter
        for karakter in metin
        if not unicodedata.combining(
            karakter
        )
    )

    ceviri = str.maketrans(
        {
            "ı": "i",
            "ş": "s",
            "ğ": "g",
            "ü": "u",
            "ö": "o",
            "ç": "c",
        }
    )

    return (
        metin
        .translate(
            ceviri
        )
        .strip()
    )
'''.strip("\n")


if marker not in text:
    hedef = '''def _onem_belirle(
'''

    if hedef not in text:
        raise RuntimeError(
            "KAP önem belirleme fonksiyonu bulunamadı."
        )

    text = text.replace(
        hedef,
        normalizer
        + "\n\n\n"
        + hedef,
        1,
    )


old_metin = '''    metin = " ".join(
        (
            baslik,
            bildirim_turu,
            ozet,
        )
    ).casefold()
'''

new_metin = '''    metin = _arama_metni(
        " ".join(
            (
                baslik,
                bildirim_turu,
                ozet,
            )
        )
    )
'''

if old_metin in text:
    text = text.replace(
        old_metin,
        new_metin,
        1,
    )
elif "_arama_metni(" not in text:
    raise RuntimeError(
        "KAP önem metni oluşturma bölümü bulunamadı."
    )


degisimler = {
    '"yeni iş ilişkisi",': (
        '"yeni is iliskisi",'
    ),
    '"sermaye artır",': (
        '"sermaye artir",'
    ),
    '"temettü",': (
        '"temettu",'
    ),
    '"pay geri alım",': (
        '"pay geri alim",'
    ),
    '"birleşme",': (
        '"birlesme",'
    ),
    '"yatırım",': (
        '"yatirim",'
    ),
    '"finansal rapor",': (
        '"finansal rapor",'
    ),
    '"faaliyet durdur",': (
        '"faaliyet durdur",'
    ),
    '"işlem sırası kapat",': (
        '"islem sirasi kapat",'
    ),
    '"temerrüt",': (
        '"temerrut",'
    ),
    '"tasfiye",': (
        '"tasfiye",'
    ),
    '"yönetim kurulu",': (
        '"yonetim kurulu",'
    ),
    '"genel kurul",': (
        '"genel kurul",'
    ),
    '"özel durum",': (
        '"ozel durum",'
    ),
    '"sözleşme",': (
        '"sozlesme",'
    ),
}

for eski, yeni in degisimler.items():
    text = text.replace(
        eski,
        yeni,
    )


path.write_text(
    text,
    encoding="utf-8",
)

ast.parse(
    path.read_text(
        encoding="utf-8",
    )
)

print(
    "KAP_TURKCE_METIN_ESLESTIRMESI_DUZELTILDI"
)
