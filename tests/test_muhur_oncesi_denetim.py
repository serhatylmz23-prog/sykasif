from syk_core.entegrasyon.muhur_oncesi_denetim import (
    MuhurOncesiDenetim,
)



def test_muhur_oncesi_denetim():

    sistem = MuhurOncesiDenetim()


    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        [

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

        ],

    )


    assert (
        sonuc.durum
        ==
        "bagimsiz_dogrulandi"
    )


    assert (
        sonuc.toplam_sprint
        ==
        16
    )


    assert (
        len(
            sonuc.eksik_sprint
        )
        ==
        0
    )
