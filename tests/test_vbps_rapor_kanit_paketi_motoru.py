from syk_core.entegrasyon.vbps_rapor_kanit_paketi_motoru import (
    VBPSRaporKanitPaketiMotoru,
)



def test_vbps_rapor():

    sistem = VBPSRaporKanitPaketiMotoru()


    sonuc = sistem.olustur(

        "RAPOR-001",

        "GARMIN_GT23",

        "AKDENIZ_SAHA",

        "SONAR_VERISI",

        "DOGRULANDI",

    )


    assert (
        sonuc.durum
        ==
        "KANIT_PAKETI_HAZIR"
    )


    assert (
        sonuc.dogrulama_durumu
        ==
        "DOGRULANDI"
    )


    assert (
        len(
            sonuc.kanit_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True
