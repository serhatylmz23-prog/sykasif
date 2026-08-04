from pathlib import Path
import ast


path = Path(
    "src/syk_finans_otagi/portfoy.py"
)

text = path.read_text(
    encoding="utf-8",
)

old = '''        kayit = PortfoyKaydi(
            **kanit,
            varlik_turu=varlik_turu,
            kayit_sha256=sha256(
                kodlu
            ).hexdigest(),
        )
'''

new = '''        kayit = PortfoyKaydi(
            kayit_id=kayit_id,
            sembol=sembol.upper(),
            varlik_turu=varlik_turu,
            islem_tarihi=tarih,
            miktar=miktar_degeri,
            birim_fiyat=fiyat,
            komisyon=komisyon_degeri,
            kaynak=kaynak,
            kayit_sha256=sha256(
                kodlu
            ).hexdigest(),
        )
'''

if old not in text:
    if (
        "miktar=miktar_degeri,"
        in text
        and "varlik_turu=varlik_turu,"
        in text
    ):
        print(
            "SYFINANS_PORTFOY_KAYDI_ZATEN_DUZELTILMIS"
        )
    else:
        raise RuntimeError(
            "Portföy kayıt oluşturma bölümü bulunamadı."
        )
else:
    text = text.replace(
        old,
        new,
        1,
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
    "SYFINANS_PORTFOY_KAYDI_DUZELTILDI"
)
