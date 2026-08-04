from pathlib import Path
import ast


path = Path(
    "src/syk_finans_otagi/sykasif_arge.py"
)

text = path.read_text(
    encoding="utf-8",
)

old = '''        ilk = sirali[0].fiyat
        son = sirali[-1].fiyat

        if ilk <= 0:
            return None

        return round(
            float(
                (
                    son - ilk
                )
                / ilk
                * Decimal("100")
            ),
            3,
        )
'''

new = '''        ilk = Decimal(
            str(
                sirali[0].fiyat
            )
        )

        son = Decimal(
            str(
                sirali[-1].fiyat
            )
        )

        if ilk <= 0:
            return None

        degisim = (
            (
                son - ilk
            )
            / ilk
            * Decimal("100")
        )

        return round(
            float(
                degisim
            ),
            3,
        )
'''

if old not in text:
    if (
        "degisim = ("
        in text
        and "sirali[0].fiyat"
        in text
        and "Decimal(" in text
    ):
        print(
            "ARGE_FIYAT_TURU_ZATEN_DUZELTILMIS"
        )
    else:
        raise RuntimeError(
            "Fiyat değişim hesabı bulunamadı."
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
    "ARGE_FIYAT_TURU_DUZELTILDI"
)
