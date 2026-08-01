from syk_core.entegrasyon.vbps_goruntu_sensor_veri_motoru import (
    VBPSGoruntuSensorVeriMotoru,
)



def test_goruntu_sensor_veri():

    sistem = VBPSGoruntuSensorVeriMotoru()


    sonuc = sistem.kaydet(

        "GORUNTU-001",

        "DRONE-001",

        "DRONE_KAMERA",

        "GORUNTU_VERISI",

        "DOGRULANDI",

        "GPS_ALANI",

    )


    assert (
        sonuc.analiz_durumu
        ==
        "ANALIZE_HAZIR"
    )


    assert (
        sonuc.kaynak_dogrulama
        ==
        "DOGRULANDI"
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
