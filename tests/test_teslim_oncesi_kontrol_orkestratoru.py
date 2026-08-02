from syk_core.entegrasyon.teslim_oncesi_kontrol_orkestratoru import (
    TeslimOncesiKontrolOrkestratoru,
)



def test_teslim_hazir_kontrol():

    sistem = TeslimOncesiKontrolOrkestratoru()


    sonuc = sistem.calistir(

        "SYK-CORE-001",

        {

            "KANIT_KONTROL":
                True,

            "SHA_KONTROL":
                True,

            "DURUM_KONTROL":
                True,

            "MUHUR_KONTROL":
                True,

        },

    )


    assert (
        sonuc.durum
        ==
        "teslime_hazir"
    )


    assert (
        sonuc.toplam_kontrol
        ==
        4
    )


    assert (
        sonuc.basarisiz_kontrol
        ==
        0
    )



def test_teslim_inceleme():

    sistem = TeslimOncesiKontrolOrkestratoru()


    sonuc = sistem.calistir(

        "SYK-CORE-001",

        {

            "KANIT_KONTROL":
                True,

            "SHA_KONTROL":
                False,

            "MUHUR_KONTROL":
                True,

        },

    )


    assert (
        sonuc.durum
        ==
        "inceleme_gerekli"
    )


    assert (
        sonuc.basarisiz_kontrol
        ==
        1
    )


    assert (
        "SHA_KONTROL"
        in
        sonuc.eksikler
    )
