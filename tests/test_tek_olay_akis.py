from syk_core.entegrasyon.tek_olay_akis import (
    TekOlayAkisYoneticisi,
)


def test_tek_olay_akisi():

    yonetici = TekOlayAkisYoneticisi()

    yonetici.olay_olustur(
        "OLAY-CORE-001"
    )

    yonetici.kanit_ekle(
        "OLAY-CORE-001",
        "KANIT-001",
    )

    yonetici.goruntu_ekle(
        "OLAY-CORE-001",
        "GOR-001",
    )

    yonetici.materyal_ekle(
        "OLAY-CORE-001",
        "ALTIN-ADAY",
    )

    yonetici.konsensus_ekle(
        "OLAY-CORE-001",
        "85-PUAN",
    )

    yonetici.tamamla(
        "OLAY-CORE-001"
    )


    sonuc = yonetici.getir(
        "OLAY-CORE-001"
    )


    assert (
        len(sonuc.kanitlar)
        ==
        1
    )

    assert (
        len(sonuc.goruntuler)
        ==
        1
    )

    assert (
        len(sonuc.materyaller)
        ==
        1
    )

    assert (
        len(sonuc.konsensuslar)
        ==
        1
    )

    assert (
        sonuc.durum
        ==
        "degerlendirildi"
    )
