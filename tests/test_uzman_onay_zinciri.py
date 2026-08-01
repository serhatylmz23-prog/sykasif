from syk_core.uzmanlar.uzman_yetki_modeli import (
    UzmanYetki,
    karar_kontrolu,
)

from syk_core.uzmanlar.onay_zinciri import (
    OnayZinciri,
)


def test_uzman_karar_yetkisi_yoktur():

    yetki = UzmanYetki(
        uzman_kimligi="JEO-001"
    )

    assert karar_kontrolu(
        yetki
    )


def test_onay_zinciri_bekleme():

    zincir = OnayZinciri()

    kayit = zincir.uzman_onerisi_al(
        "materyal analizi",
        "metal izi olabilir",
    )

    assert (
        zincir.nihai_karar(kayit)
        ==
        "beklemede"
    )


def test_kasif_ve_bilge_kaan_onayi():

    zincir = OnayZinciri()

    kayit = zincir.uzman_onerisi_al(
        "alan inceleme",
        "ileri analiz gerekli",
    )

    zincir.bilge_kaan_degerlendir(
        kayit,
        "onay",
    )

    zincir.kasif_degerlendir(
        kayit,
        "onay",
    )

    assert (
        zincir.nihai_karar(kayit)
        ==
        "yururluk"
    )
