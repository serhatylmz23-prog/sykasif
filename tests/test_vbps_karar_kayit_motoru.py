from syk_core.entegrasyon.vbps_karar_kayit_motoru import (
    VBPSKararKayitMotoru,
)



def test_vbps_kayit():

    sistem = VBPSKararKayitMotoru()


    sonuc = sistem.kaydet(

        "VBPS-001",

        "BALIK_BULUCU",

        "WIFI",

        "DOGRULANDI",

        "MANUEL_OTONOM_DESTEKLI",

        "YETERLI",

        "YOK",

        "ONAYLANDI",

        "ANALIZ_DEVAM_EDIYOR",

    )


    assert (
        sonuc.onay_durumu
        ==
        "ONAYLANDI"
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
