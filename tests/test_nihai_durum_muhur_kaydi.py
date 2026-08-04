from syk_core.entegrasyon.nihai_durum_muhur_kaydi import (
    NihaiDurumMuhurKayitMotoru,
)



def test_nihai_muhur_kaydi():

    sistem = NihaiDurumMuhurKayitMotoru()


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
        "SPRINT-073",

    ]


    katmanlar = [

        "SHA",
        "MANIFEST",
        "ARTEFAKT",
        "KANIT",
        "MUHUR",
        "BAGIMSIZ_DOGRULAMA",

    ]


    sonuc = sistem.muhur_olustur(

        "SYK-CORE-001",

        "son_muhur_adayi",

        "nihai_muhur_kaydi",

        sprintler,

        katmanlar,

        "kurucu_onayi_bekliyor",

    )


    assert (
        sonuc.durum
        ==
        "nihai_muhur_kaydi"
    )


    assert (
        sonuc.toplam_sprint
        ==
        20
    )


    assert (
        sonuc.toplam_katman
        ==
        6
    )


    assert (
        sonuc.karar_durumu
        ==
        "kurucu_onayi_bekliyor"
    )


    assert (
        len(
            sonuc.muhur_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(

        sonuc,

        sprintler,

        katmanlar,

        "kurucu_onayi_bekliyor",

    ) is True
