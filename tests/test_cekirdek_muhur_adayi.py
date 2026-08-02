from syk_core.entegrasyon.cekirdek_muhur_adayi import (
    CekirdekMuhurAdayi,
)



def test_cekirdek_muhur_adayi():


    sistem = CekirdekMuhurAdayi()



    sonuc = sistem.olustur(

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
        ],

    )



    assert (
        sonuc.durum
        ==
        "muhur_adayi"
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
            "SYK-CORE-001"
        )
        is True
    )
