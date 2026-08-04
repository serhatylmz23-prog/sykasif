from syk_core.entegrasyon.kalici_teslim_manifesti import (
    KaliciTeslimManifesti,
)



def test_kalici_teslim_manifesti():

    sistem = KaliciTeslimManifesti()


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

    ]


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        sprintler,

    )


    assert (
        sonuc.durum
        ==
        "kalici_teslim_adayi"
    )


    assert (
        sonuc.sprint_sayisi
        ==
        17
    )


    assert (
        len(
            sonuc.manifest_hashi
        )
        ==
        64
    )


    assert (
        sistem.dogrula(
            "SYK-CORE-001",
            sprintler,
        )
        is True
    )
