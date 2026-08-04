from syk_core.entegrasyon.kalici_teslim_arsivi_olusturma_motoru import (
    KaliciTeslimArsiviOlusturmaMotoru,
)



def test_kalici_teslim_arsivi():

    sistem = KaliciTeslimArsiviOlusturmaMotoru()


    kayitlar = [

        "SPRINT-075",
        "SPRINT-076",
        "SPRINT-077",
        "SPRINT-078",
        "SPRINT-079",
        "SPRINT-080",
        "SPRINT-081",
        "SPRINT-082",
        "SPRINT-083",
        "SPRINT-084",
        "SPRINT-085",

    ]


    kontroller = {

        "ARTEFAKT_ZINCIRI":
            True,

        "SHA256_KAPANIS":
            True,

        "MANIFEST":
            True,

        "TESLIM_PAKETI":
            True,

        "BAGIMSIZ_DOGRULAMA":
            True,

        "NIHAI_ZINCIR":
            True,

        "KAPANIS_MUHUR":
            True,

        "SON_RAPOR":
            True,

    }



    sonuc = sistem.olustur(

        "SYK-CORE-001",

        kayitlar,

        kontroller,

    )



    assert (

        sonuc.durum

        ==

        "kalici_teslim_arsivi_hazir"

    )


    assert (

        sonuc.toplam_kayit

        ==

        11

    )


    assert (

        sonuc.toplam_kontrol

        ==

        8

    )


    assert (

        sonuc.basarili_kontrol

        ==

        8

    )


    assert (

        sonuc.hatali_kontrol

        ==

        0

    )


    assert (

        len(
            sonuc.arsiv_sha256
        )

        ==

        64

    )


    assert sistem.dogrula(

        sonuc,

        kayitlar,

        kontroller,

    ) is True
