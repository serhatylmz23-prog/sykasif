from syk_core.entegrasyon.tek_olay_rapor_paketleyici import (
    TekOlayRaporPaketleyici,
)



def test_tam_rapor_paketi():

    motor = TekOlayRaporPaketleyici()


    paket = motor.olustur(
        "OLAY-046",
        [
            "KANIT-A",
            "KANIT-B",
        ],
        [
            "GORUNTU_UZMANI",
            "MATERYAL_UZMANI",
        ],
        "guclu_destek",
        92,
        [
            "Kan?t sayisi yeterli",
            "Uzman uyumu mevcut",
        ],
    )


    assert (
        paket.olay_kimligi
        ==
        "OLAY-046"
    )


    assert (
        len(
            paket.kanitlar
        )
        ==
        2
    )


    assert (
        len(
            paket.uzman_sonuclari
        )
        ==
        2
    )


    assert (
        paket.karar
        ==
        "guclu_destek"
    )


    assert (
        paket.guven_puani
        ==
        92
    )


    assert (
        paket.durum
        ==
        "hazir"
    )
