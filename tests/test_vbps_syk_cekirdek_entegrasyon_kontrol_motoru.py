from syk_core.entegrasyon.vbps_syk_cekirdek_entegrasyon_kontrol_motoru import (
    VBPSYKCekirdekEntegrasyonKontrolMotoru,
)



def test_entegrasyon_kontrol():

    sistem = VBPSYKCekirdekEntegrasyonKontrolMotoru()


    sonuc = sistem.kontrol_et(

        "ENTEGRASYON-001",

        "HAZIR",

        "HAZIR",

        "HAZIR",

        "HAZIR",

    )


    assert (
        sonuc.zincir_durumu
        ==
        "ENTEGRASYON_TAMAM"
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
