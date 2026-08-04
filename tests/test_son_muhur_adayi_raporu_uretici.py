from syk_core.entegrasyon.son_muhur_adayi_raporu_uretici import (
    SonMuhurAdayiRaporUretici,
)



def test_son_muhur_adayi():

    sistem = SonMuhurAdayiRaporUretici()


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
        "SPRINT-072",

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

        "son_arsiv_teslim_adayi",

    )


    assert (
        sonuc.durum
        ==
        "son_muhur_adayi"
    )


    assert (
        sonuc.toplam_sprint
        ==
        19
    )


    assert (
        sonuc.toplam_katman
        ==
        6
    )


    assert (
        len(
            sonuc.rapor_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(

        sonuc,

        sprintler,

        katmanlar,

        "tam_dogrulandi",

        "son_arsiv_teslim_adayi",

    ) is True
