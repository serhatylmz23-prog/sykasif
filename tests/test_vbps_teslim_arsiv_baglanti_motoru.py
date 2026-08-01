from syk_core.entegrasyon.vbps_teslim_arsiv_baglanti_motoru import (
    VBPSTeslimArsivBaglantiMotoru,
)



def test_teslim_arsiv():

    sistem = VBPSTeslimArsivBaglantiMotoru()


    sonuc = sistem.bagla(

        "TESLIM-001",

        "RAPOR-001",

        "KANIT-001",

        "ARSIV-001",

    )


    assert (
        sonuc.durum
        ==
        "TESLIM_ZINCIRI_HAZIR"
    )


    assert (
        sonuc.rapor_id
        ==
        "RAPOR-001"
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
