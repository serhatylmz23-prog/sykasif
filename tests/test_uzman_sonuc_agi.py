from syk_core.entegrasyon.uzman_sonuc_agi import (
    UzmanSonucAgMotoru,
)



def test_uzman_sonuc_agi():

    sistem = UzmanSonucAgMotoru()


    sistem.olay_olustur(
        "OLAY-042"
    )


    sistem.kanit_bagla(
        "OLAY-042",
        "KANIT-042",
    )


    sistem.uzman_sonucu_ekle(
        "OLAY-042",
        "GORUNTU_UZMANI",
        "UYUMLU",
        90,
    )


    sistem.uzman_sonucu_ekle(
        "OLAY-042",
        "MATERYAL_UZMANI",
        "UYUMLU",
        80,
    )


    sonuc = sistem.getir(
        "OLAY-042"
    )


    assert len(
        sonuc.kanitlar
    ) == 1


    assert len(
        sonuc.uzman_sonuclari
    ) == 2


    assert (
        sistem.konsensus_hesapla(
            "OLAY-042"
        )
        ==
        85
    )
