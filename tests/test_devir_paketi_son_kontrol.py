from syk_core.entegrasyon.devir_paketi_son_kontrol import (
    DevirPaketiSonKontrol,
)



def test_devir_paketi_son_kontrol():

    sistem = DevirPaketiSonKontrol()


    sprintler = [

        "SPRINT-035",
        "SPRINT-036",
        "SPRINT-037",
        "SPRINT-038",
        "SPRINT-039",
        "SPRINT-040",
        "SPRINT-041",
        "SPRINT-042",
        "SPRINT-043",
        "SPRINT-044",
        "SPRINT-045",
        "SPRINT-046",
        "SPRINT-047",
        "SPRINT-048",
        "SPRINT-049",
        "SPRINT-050",
        "SPRINT-051",
        "SPRINT-052",

    ]


    moduller = [

        "HASH",
        "KANIT",
        "UZMAN_AGI",
        "RAPOR",
        "MUHUR",
        "MANIFEST",

    ]


    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        sprintler,

        moduller,

    )


    assert (
        sonuc.durum
        ==
        "devir_adayi_hazir"
    )


    assert (
        sonuc.kontrol_edilen_sprint
        ==
        18
    )


    assert (
        len(
            sonuc.eksik_sprint
        )
        ==
        0
    )


    assert (
        sonuc.modul_sayisi
        ==
        6
    )
