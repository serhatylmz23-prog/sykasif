from syk_core.entegrasyon.vbps_saha_hafiza_karsilastirma_motoru import (
    VBPSSahaHafizaKarsilastirmaMotoru,
)



def test_saha_hafiza():

    sistem = VBPSSahaHafizaKarsilastirmaMotoru()


    sonuc = sistem.karsilastir(

        "SAHA-HAFIZA-001",

        "SONAR_KAYIT_A",

        "SONAR_KAYIT_B",

        "AKDENIZ_SAHA",

    )


    assert (
        sonuc.degisim_durumu
        ==
        "DEGISIM_VAR"
    )


    assert (
        sonuc.analiz_durumu
        ==
        "KARSILASTIRMA_TAMAM"
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
