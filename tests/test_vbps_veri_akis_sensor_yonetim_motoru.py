from syk_core.entegrasyon.vbps_veri_akis_sensor_yonetim_motoru import (
    VBPSVeriAkisSensorYonetimMotoru,
)



def test_vbps_veri():

    sistem = VBPSVeriAkisSensorYonetimMotoru()


    sonuc = sistem.veri_kaydet(

        "VERI-001",

        "CIHAZ-001",

        "SONAR",

        "BALIK_BULUCU_VERISI",

        "YETERLI",

    )


    assert (
        sonuc.analiz_hazirligi
        ==
        "ANALIZE_HAZIR"
    )


    assert (
        sonuc.veri_durumu
        ==
        "YETERLI"
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
