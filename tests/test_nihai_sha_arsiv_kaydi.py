from syk_core.entegrasyon.nihai_sha_arsiv_kaydi import (
    NihaiSHAArsivKaydi,
)



def test_nihai_sha_arsiv_kaydi():


    sistem = NihaiSHAArsivKaydi()


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
        "SPRINT-057",

    ]



    sonuc = sistem.arsiv_olustur(

        "SYK-CORE-001",

        sprintler,

    )


    assert (
        sonuc.durum
        ==
        "bagimsiz_sha_arsiv_kaydi"
    )


    assert (
        sonuc.zincir_baslangic
        ==
        "SPRINT-035"
    )


    assert (
        sonuc.zincir_bitis
        ==
        "SPRINT-057"
    )


    assert (
        sonuc.toplam_kayit
        ==
        23
    )


    assert (
        len(
            sonuc.arsiv_sha256
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
