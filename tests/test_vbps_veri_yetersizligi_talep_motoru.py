from syk_core.entegrasyon.vbps_veri_yetersizligi_talep_motoru import (
    VBPSVeriYetersizligiTalepMotoru,
)



def test_veri_yetersizligi():

    sistem = VBPSVeriYetersizligiTalepMotoru()


    sonuc = sistem.kaydet(

        "TALEP-001",

        "YETERSIZ",

        "TERMAL_KAMERA",

        "TALEP_EDILDI",

        "GPS_KAYITLI_ALAN",

        "BEKLIYOR",

    )


    assert (
        sonuc.sonuc
        ==
        "EK_VERI_VEYA_CIHAZ_GEREKLI"
    )


    assert (
        sonuc.onay_durumu
        ==
        "BEKLIYOR"
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
