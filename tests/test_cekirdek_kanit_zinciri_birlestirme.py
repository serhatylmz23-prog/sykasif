from syk_core.entegrasyon.cekirdek_kanit_zinciri_birlestirme import (
    CekirdekKanitZinciriBirlestirme,
)



def test_cekirdek_kanit_zinciri():

    sistem = CekirdekKanitZinciriBirlestirme()


    sonuc = sistem.birlestir(

        "SYK-CORE-001",

        "KANIT-SHA-001",

        "DURUM-SHA-001",

        "MANIFEST-SHA-001",

        "MUHUR-SHA-001",

    )


    assert (
        sonuc.durum
        ==
        "birlesik_zincir_hazir"
    )


    assert (
        sonuc.toplam_bilesen
        ==
        4
    )


    assert (
        len(
            sonuc.zincir_hashi
        )
        ==
        64
    )


    assert (
        sistem.dogrula(
            "SYK-CORE-001"
        )
        is True
    )
