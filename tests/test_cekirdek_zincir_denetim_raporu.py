from syk_core.entegrasyon.cekirdek_zincir_denetim_raporu import (
    CekirdekZincirDenetimRaporuUretici,
)



def test_zincir_saglikli_denetim():

    sistem = CekirdekZincirDenetimRaporuUretici()


    sonuc = sistem.denetle(

        "SYK-CORE-001",

        [

            "KANIT",

            "SHA",

            "MANIFEST",

            "MUHUR",

        ],

        lambda x: True,

    )


    assert (
        sonuc.durum
        ==
        "zincir_saglikli"
    )


    assert (
        sonuc.toplam_bilesen
        ==
        4
    )


    assert (
        sonuc.basarili_kontrol
        ==
        4
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
    )



def test_zincir_risk_tespiti():

    sistem = CekirdekZincirDenetimRaporuUretici()


    sonuc = sistem.denetle(

        "SYK-CORE-001",

        [

            "KANIT",

            "BOZUK_HASH",

            "MUHUR",

        ],

        lambda x: x != "BOZUK_HASH",

    )


    assert (
        sonuc.durum
        ==
        "zincir_riskli"
    )


    assert (
        sonuc.hatali_kontrol
        ==
        1
    )


    assert (
        "BOZUK_HASH"
        in
        sonuc.riskler
    )
