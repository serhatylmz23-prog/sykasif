from syk_core.entegrasyon.devir_nihai_durum_raporu import (
    DevirNihaiDurumRaporu,
)



def test_devir_nihai_durum_raporu():


    sistem = DevirNihaiDurumRaporu()



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



    sonuc = sistem.olustur(

        "SYK-CORE-001",

        sprintler,

        moduller,

    )



    assert (

        sonuc.durum

        ==

        "devir_raporu_hazir"

    )



    assert (

        sonuc.sprint_sayisi

        ==

        20

    )



    assert (

        sonuc.modul_sayisi

        ==

        8

    )



    assert (

        len(
            sonuc.rapor_hashi
        )

        ==

        64

    )



    assert (

        sistem.dogrula(

            "SYK-CORE-001",

            sprintler,

            moduller,

        )

        is True

    )
