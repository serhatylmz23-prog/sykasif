from syk_core.entegrasyon.son_teslim_butunsel_muhur_raporu import (
    SonTeslimButunselMuhurRaporUretici,
)



def test_son_teslim_butunsel():

    sistem = SonTeslimButunselMuhurRaporUretici()


    sprintler = [

        "SPRINT-075",
        "SPRINT-076",
        "SPRINT-077",
        "SPRINT-078",
        "SPRINT-079",
        "SPRINT-080",
        "SPRINT-081",
        "SPRINT-082",
        "SPRINT-083",
        "SPRINT-084",

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

        "KAPANIS_MUHUR":
            True,

    }



    sonuc = sistem.olustur(

        "SYK-CORE-001",

        sprintler,

        kontroller,

        "kapanis_zinciri_hazir",

    )



    assert (

        sonuc.durum

        ==

        "son_teslim_butunsel_dogrulandi"

    )


    assert (

        sonuc.toplam_sprint

        ==

        10

    )


    assert (

        sonuc.toplam_kontrol

        ==

        7

    )


    assert (

        sonuc.basarili_kontrol

        ==

        7

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

        "kapanis_zinciri_hazir",

    ) is True
