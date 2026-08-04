from syk_core.entegrasyon.syk_cihaz_eslesme_yetkilendirme_motoru import (
    SYKCihazEslesmeYetkilendirmeMotoru,
)



def test_cihaz_eslesme():

    sistem = SYKCihazEslesmeYetkilendirmeMotoru()


    sonuc = sistem.cihaz_kaydet(

        "CIHAZ-001",

        "BALIK_BULUCU",

        "WIFI",

        "GARMIN_GT23",

    )


    assert (
        sonuc.eslesme_durumu
        ==
        "ESLESME_TAMAM"
    )


    assert (
        sonuc.yetki_durumu
        ==
        "YETKILI"
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
