from syk_core.entegrasyon.son_muhur_entegrasyon_kontrolu import (
    SonMuhurEntegrasyonKontrolu,
)



def test_son_muhur_kontrolu():


    sistem = SonMuhurEntegrasyonKontrolu()



    sonuc = sistem.kontrol_et(

        "OLAY-049",

        [
            "KANIT-A",
            "KANIT-B",
        ],

        [
            "GORUNTU",
            "MATERYAL",
            "JEOLOJI",
        ],

        "guclu_destek",

        94,

        "a" * 64,

        "b" * 64,

    )



    assert (
        sonuc.durum
        ==
        "dogrulandi"
    )



    assert (
        sonuc.olay_kimligi
        ==
        "OLAY-049"
    )



    assert (
        sonuc.kanit_sayisi
        ==
        2
    )



    assert (
        sonuc.uzman_sayisi
        ==
        3
    )
