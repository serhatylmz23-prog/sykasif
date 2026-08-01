from syk_core.entegrasyon.vbps_operasyon_komuta_motoru import (
    VBPSOperasyonKomutaMotoru,
)



def test_vbps_komuta():

    sistem = VBPSOperasyonKomutaMotoru()


    sonuc = sistem.komut_kaydet(

        "KOMUT-001",

        "ROBOT_KAMERA_001",

        "MANUEL_OTONOM_DESTEKLI",

        "SAGA_DON",

        "SAG",

        "ONAYLANDI",

    )


    assert (
        sonuc.sonuc
        ==
        "KOMUT_UYGULAMA_HAZIR"
    )


    assert (
        sonuc.kullanim_modu
        ==
        "MANUEL_OTONOM_DESTEKLI"
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
