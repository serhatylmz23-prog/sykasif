from syk_core.entegrasyon.kanit_guven_konsensus import (
    KanitGuvenKonsensusBaglantisi,
)


def test_kanit_guven_konsensus():

    sistem = (
        KanitGuvenKonsensusBaglantisi()
    )


    sistem.olay_kaydet(
        "OLAY-023"
    )


    sistem.kanit_ekle(
        "OLAY-023",
        "KANIT-001",
    )


    sistem.guven_puani_ekle(
        "OLAY-023",
        90,
    )


    sistem.konsensus_puani_ekle(
        "OLAY-023",
        80,
    )


    sonuc = sistem.degerlendir(
        "OLAY-023"
    )


    assert len(
        sonuc.kanitlar
    ) == 1


    assert (
        sonuc.durum
        ==
        "guclu_destek"
    )
