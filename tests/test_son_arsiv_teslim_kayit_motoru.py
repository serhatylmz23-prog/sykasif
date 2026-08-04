from syk_core.entegrasyon.son_arsiv_teslim_kayit_motoru import (
    SonArsivTeslimKayitMotoru,
)



def test_son_arsiv_teslim_kaydi():

    sistem = SonArsivTeslimKayitMotoru()


    sprintler = [

        "SPRINT-054",
        "SPRINT-055",
        "SPRINT-056",
        "SPRINT-057",
        "SPRINT-058",
        "SPRINT-059",
        "SPRINT-060",
        "SPRINT-061",
        "SPRINT-062",
        "SPRINT-063",
        "SPRINT-064",
        "SPRINT-065",
        "SPRINT-066",
        "SPRINT-067",
        "SPRINT-068",
        "SPRINT-069",
        "SPRINT-070",
        "SPRINT-071",

    ]


    katmanlar = [

        "SHA",
        "MANIFEST",
        "ARTEFAKT",
        "KANIT",
        "MUHUR",
        "BAGIMSIZ_DOGRULAMA",

    ]


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        sprintler,

        katmanlar,

        "tam_dogrulandi",

    )


    assert (
        sonuc.durum
        ==
        "son_arsiv_teslim_adayi"
    )


    assert (
        sonuc.toplam_sprint
        ==
        18
    )


    assert (
        sonuc.toplam_katman
        ==
        6
    )


    assert (
        len(
            sonuc.teslim_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(

        sonuc,

        sprintler,

        katmanlar,

        "tam_dogrulandi",

    ) is True
