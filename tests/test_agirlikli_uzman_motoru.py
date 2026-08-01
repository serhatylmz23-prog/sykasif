from syk_core.entegrasyon.agirlikli_uzman_motoru import (
    AgirlikliUzmanKararMotoru,
)



def test_agirlikli_uzman_motoru():

    sistem = AgirlikliUzmanKararMotoru()


    sistem.olay_olustur(
        "OLAY-043"
    )


    sistem.kanit_ekle(
        "OLAY-043",
        "KANIT-043",
    )


    sistem.uzman_ekle(
        "OLAY-043",
        "GORUNTU_UZMANI",
        "UYUMLU",
        90,
        0.25,
    )


    sistem.uzman_ekle(
        "OLAY-043",
        "MATERYAL_UZMANI",
        "UYUMLU",
        80,
        0.30,
    )


    sistem.uzman_ekle(
        "OLAY-043",
        "JEOLOJI_UZMANI",
        "UYUMLU",
        85,
        0.45,
    )


    sonuc = sistem.agirlikli_konsensus(
        "OLAY-043"
    )


    assert (
        sonuc
        ==
        84.75
    )


    kayit = sistem.getir(
        "OLAY-043"
    )


    assert len(
        kayit.uzmanlar
    ) == 3
