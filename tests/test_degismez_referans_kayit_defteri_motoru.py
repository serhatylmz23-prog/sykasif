from syk_core.entegrasyon.degismez_referans_kayit_defteri_motoru import (
    DegismezReferansKayitDefteriMotoru,
)



def test_degismez_referans_kaydi():

    sistem = DegismezReferansKayitDefteriMotoru()


    sonuc = sistem.kaydet(

        "SYK-CORE-001",

        "SYK_CORE_REFERANS_MUHUR_001",

        "a" * 64,

        "b" * 64,

        "son_muhur_guncelleme",

        "v1.0",

    )


    assert (
        sonuc.durum
        ==
        "degismez_referans_kaydi_hazir"
    )


    assert (
        sonuc.degisim_tipi
        ==
        "son_muhur_guncelleme"
    )


    assert (
        sonuc.surum_bilgisi
        ==
        "v1.0"
    )


    assert (
        len(
            sonuc.kayit_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True
