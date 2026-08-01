from syk_core.entegrasyon.cekirdek_kanit_zinciri_sonuc_raporu import (
    CekirdekKanitZinciriSonucRaporuUretici,
)



def test_sonuc_raporu_onayli():

    sistem = CekirdekKanitZinciriSonucRaporuUretici()


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        "zincir_saglikli",

        4,

        4,

        0,

        [],

    )


    assert (
        sonuc.durum
        ==
        "sonuc_onayli"
    )


    assert (
        len(
            sonuc.sonuc_hashi
        )
        ==
        64
    )


    assert (
        sistem.dogrula(
            sonuc
        )
        is True
    )



def test_sonuc_inceleme():

    sistem = CekirdekKanitZinciriSonucRaporuUretici()


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        "zincir_riskli",

        4,

        3,

        1,

        [
            "BOZUK_HASH"
        ],

    )


    assert (
        sonuc.durum
        ==
        "sonuc_inceleme_gerekli"
    )


    assert (
        sonuc.hatali_kontrol
        ==
        1
    )
