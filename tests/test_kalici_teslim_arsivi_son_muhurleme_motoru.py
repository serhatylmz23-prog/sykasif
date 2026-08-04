from syk_core.entegrasyon.kalici_teslim_arsivi_son_muhurleme_motoru import (
    KaliciTeslimArsiviSonMuhurlemeMotoru,
)



def test_kalici_son_muhur():

    sistem = KaliciTeslimArsiviSonMuhurlemeMotoru()


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

        "KALICI_ARSIV":
            True,

        "YENIDEN_DOGRULAMA":
            True,

    }



    sonuc = sistem.muhurle(

        "SYK-CORE-001",

        "kalici_teslim_arsivi_hazir",

        kontroller,

    )



    assert (
        sonuc.durum
        ==
        "kalici_teslim_arsivi_son_muhur_tamam"
    )


    assert (
        sonuc.toplam_kontrol
        ==
        10
    )


    assert (
        sonuc.basarili_kontrol
        ==
        10
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
    )


    assert (
        len(
            sonuc.son_muhur_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(

        sonuc,

        kontroller,

    ) is True
