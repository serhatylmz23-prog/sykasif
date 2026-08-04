from pathlib import Path

from syk_core.entegrasyon.gercek_dosya_sha_tarayici import (
    GercekDosyaSHATarayici,
)



def test_gercek_sha_tarama():

    gecici = Path(
        "test_sha_ornek.txt"
    )

    gecici.write_text(
        "SYK-CORE-001",
        encoding="utf-8",
    )


    sistem = GercekDosyaSHATarayici()


    sonuc = sistem.tara(
        str(gecici)
    )


    assert (
        sonuc.durum
        ==
        "gercek_sha_uretildi"
    )


    assert (
        len(
            sonuc.sha256
        )
        ==
        64
    )


    assert (
        sistem.dogrula(
            str(gecici)
        )
        is True
    )


    gecici.unlink()
