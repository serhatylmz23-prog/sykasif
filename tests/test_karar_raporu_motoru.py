from syk_core.entegrasyon.karar_raporu_motoru import (
    KararRaporuMotoru,
)



def test_karar_raporu():

    motor = KararRaporuMotoru()


    rapor = motor.olustur(
        "OLAY-045",
        "guclu_destek",
        92,
        [
            "KANIT-1",
            "KANIT-2",
        ],
        [
            "GORUNTU_UZMANI",
            "MATERYAL_UZMANI",
        ],
    )


    assert (
        rapor.olay_kimligi
        ==
        "OLAY-045"
    )


    assert (
        rapor.karar
        ==
        "guclu_destek"
    )


    assert (
        rapor.guven_puani
        ==
        92
    )


    assert (
        len(
            rapor.gerekceler
        )
        ==
        3
    )


    assert (
        "KANIT"
        in
        rapor.gerekceler[0].baslik
    )
