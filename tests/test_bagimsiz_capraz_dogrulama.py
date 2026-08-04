from syk_core.entegrasyon.bagimsiz_capraz_dogrulama import (
    BagimsizCaprazDogrulama,
)



def test_bagimsiz_capraz_dogrulama():


    sistem = BagimsizCaprazDogrulama()



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
        "SPRINT-053",
        "SPRINT-054",
        "SPRINT-055",

    ]



    moduller = [

        "HASH",
        "KANIT",
        "MANIFEST",
        "UZMAN_AGI",
        "KARAR",
        "RAPOR",
        "MUHUR",
        "DEVIR",

    ]



    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        sprintler,

        moduller,

    )



    assert (

        sonuc.durum

        ==

        "bagimsiz_capraz_dogrulandi"

    )



    assert (

        sonuc.kontrol_sprint_sayisi

        ==

        21

    )



    assert (

        sonuc.kontrol_modul_sayisi

        ==

        8

    )



    assert (

        len(
            sonuc.eksikler
        )

        ==

        0

    )
