from syk_core.entegrasyon.nihai_zincir_butunluk_kontrol_motoru import (
    NihaiZincirButunlukKontrolMotoru,
)



def test_nihai_zincir():

    sistem = NihaiZincirButunlukKontrolMotoru()


    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        {

            "ARTEFAKT":
                True,

            "SHA":
                True,

            "MANIFEST":
                True,

            "TESLIM_ZINCIRI":
                True,

            "TESLIM_PAKETI":
                True,

            "BAGIMSIZ_DOGRULAMA":
                True,

        },

    )


    assert (
        sonuc.durum
        ==
        "nihai_zincir_tamam"
    )


    assert (
        sonuc.toplam_kontrol
        ==
        6
    )


    assert (
        sonuc.basarili_kontrol
        ==
        6
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
    )


    assert (
        len(
            sonuc.kapanis_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(

        sonuc,

        {

            "ARTEFAKT": True,
            "SHA": True,
            "MANIFEST": True,
            "TESLIM_ZINCIRI": True,
            "TESLIM_PAKETI": True,
            "BAGIMSIZ_DOGRULAMA": True,

        },

    ) is True
