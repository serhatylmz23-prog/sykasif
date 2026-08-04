from syk_core.entegrasyon.teslim_arsivi_kapanis_muhur_motoru import (
    TeslimArsiviKapanisMuhurMotoru,
)



def test_teslim_arsivi_kapanis_muhur():

    sistem = TeslimArsiviKapanisMuhurMotoru()


    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        {

            "ARTEFAKT":
                True,

            "SHA256SUMS":
                True,

            "MANIFEST":
                True,

            "TESLIM_PAKETI":
                True,

            "BAGIMSIZ_DOGRULAMA":
                True,

            "NIHAI_ZINCIR":
                True,

            "KAPANIS_HASH":
                True,

        },

    )


    assert (
        sonuc.durum
        ==
        "teslim_arsivi_kapanis_muhur_tamam"
    )


    assert (
        sonuc.toplam_kontrol
        ==
        7
    )


    assert (
        sonuc.basarili_kontrol
        ==
        7
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
    )


    assert (
        len(
            sonuc.kapanis_muhur_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(

        sonuc,

        {

            "ARTEFAKT": True,
            "SHA256SUMS": True,
            "MANIFEST": True,
            "TESLIM_PAKETI": True,
            "BAGIMSIZ_DOGRULAMA": True,
            "NIHAI_ZINCIR": True,
            "KAPANIS_HASH": True,

        },

    ) is True
