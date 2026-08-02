from syk_core.entegrasyon.nihai_muhur_adayi_ozet import (
    NihaiMuhurAdayiOzet,
)



def test_nihai_muhur_adayi_ozet():


    sistem = NihaiMuhurAdayiOzet()


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
        "SPRINT-056",

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

        "bagimsiz_capraz_dogrulandi",

    )


    assert (
        sonuc.durum
        ==
        "nihai_muhur_adayi"
    )


    assert (
        sonuc.sprint_sayisi
        ==
        22
    )


    assert (
        sonuc.modul_sayisi
        ==
        8
    )


    assert (
        sonuc.dogrulama_durumu
        ==
        "bagimsiz_capraz_dogrulandi"
    )


    assert (
        len(
            sonuc.sha256
        )
        ==
        64
    )


    assert (
        sistem.dogrula(
            "SYK-CORE-001",
            sprintler,
            moduller,
            "bagimsiz_capraz_dogrulandi",
        )
        is True
    )
