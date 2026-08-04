from syk_core.entegrasyon.toplu_sha_manifest_muhur import (
    TopluSHAManifestMuhur,
)



def test_toplu_sha_manifest_muhur():


    sistem = TopluSHAManifestMuhur()



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



    sonuc = sistem.olustur(

        "SYK-CORE-001",

        sprintler,

    )



    assert (

        sonuc.durum

        ==

        "son_muhur_adayi"

    )



    assert (

        sonuc.sprint_sayisi

        ==

        20

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
