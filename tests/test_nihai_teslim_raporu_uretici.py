from syk_core.entegrasyon.nihai_teslim_raporu_uretici import (
    NihaiTeslimRaporUretici,
)



def test_nihai_teslim_raporu():

    sistem = NihaiTeslimRaporUretici()


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
        "SPRINT-074",
        "SPRINT-075",
        "SPRINT-076",
        "SPRINT-077",
        "SPRINT-078",
        "SPRINT-079",
        "SPRINT-080",

    ]


    kontroller = {

        "ARTEFAKT":
            True,

        "SHA":
            True,

        "MANIFEST":
            True,

        "TESLIM":
            True,

        "BAGIMSIZ_DOGRULAMA":
            True,

        "NIHAI_ZINCIR":
            True,

    }



    sonuc = sistem.olustur(

        "SYK-CORE-001",

        sprintler,

        kontroller,

    )



    assert (
        sonuc.durum
        ==
        "nihai_teslim_raporu_hazir"
    )


    assert (
        sonuc.toplam_sprint
        ==
        27
    )


    assert (
        sonuc.toplam_kontrol
        ==
        6
    )


    assert (
        sonuc.basarili_kontrol
        ==
        6
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
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

        kontroller,

    ) is True
