from syk_core.entegrasyon.import_dogrulama import (
    ImportDogrulamaMotoru,
)



def test_syk_core_importlari():

    motor = ImportDogrulamaMotoru(
        [
            "syk_core.kanit.kaynak_modeli",
            "syk_core.goruntu.goruntu_kanit_baglanti",
            "syk_core.laboratuvar.materyal_modeli",
            "syk_core.degerlendirme.birlesik_degerlendirme",
        ]
    )


    sonuc = motor.kontrol_et()


    assert (
        sonuc[
            "syk_core.kanit.kaynak_modeli"
        ]
        is True
    )


    assert (
        sonuc[
            "syk_core.goruntu.goruntu_kanit_baglanti"
        ]
        is True
    )


    assert (
        sonuc[
            "syk_core.laboratuvar.materyal_modeli"
        ]
        is True
    )


    assert (
        sonuc[
            "syk_core.degerlendirme.birlesik_degerlendirme"
        ]
        is True
    )
