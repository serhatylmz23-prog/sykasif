from syk_core.entegrasyon.tam_bagimsiz_yeniden_dogrulama_motoru import (
    TamBagimsizYenidenDogrulamaMotoru,
)



def test_tam_yeniden_dogrulama():

    sistem = TamBagimsizYenidenDogrulamaMotoru()


    sonuc = sistem.calistir(

        "SYK-CORE-001",

        {

            "SHA":
                True,

            "MANIFEST":
                True,

            "ARTEFAKT":
                True,

            "KANIT":
                True,

            "MUHUR":
                True,

            "BAGIMSIZ_KONTROL":
                True,

        },

    )


    assert (
        sonuc.durum
        ==
        "yeniden_dogrulandi"
    )


    assert (
        sonuc.toplam_katman
        ==
        6
    )


    assert (
        sonuc.basarili_katman
        ==
        6
    )


    assert (
        sonuc.hatali_katman
        ==
        0
    )


    assert (
        len(
            sonuc.zincir_hashi
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc,
        {

            "SHA": True,
            "MANIFEST": True,
            "ARTEFAKT": True,
            "KANIT": True,
            "MUHUR": True,
            "BAGIMSIZ_KONTROL": True,

        },
    ) is True



def test_hata_katmani():

    sistem = TamBagimsizYenidenDogrulamaMotoru()


    sonuc = sistem.calistir(

        "SYK-CORE-001",

        {

            "SHA":
                True,

            "MANIFEST":
                False,

            "MUHUR":
                True,

        },

    )


    assert (
        sonuc.durum
        ==
        "inceleme_gerekli"
    )


    assert (
        "MANIFEST"
        in
        sonuc.eksikler
    )
