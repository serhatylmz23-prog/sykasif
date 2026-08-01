from syk_core.entegrasyon.vbps_konum_harita_saha_motoru import (
    VBPSKonumHaritaSahaMotoru,
)



def test_vbps_konum():

    sistem = VBPSKonumHaritaSahaMotoru()


    sonuc = sistem.kaydet(

        "SAHA-001",

        "BALIK_BULUCU-001",

        36.8841,

        30.7056,

        "AKDENIZ_SAHA",

        "SONAR_VERISI",

    )


    assert (
        sonuc.tekrar_ziyaret
        ==
        "KAYITLI_SAHA"
    )


    assert (
        sonuc.saha_adi
        ==
        "AKDENIZ_SAHA"
    )


    assert (
        len(
            sonuc.sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True
