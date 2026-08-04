from syk_core.entegrasyon.kalici_olay_deposu import (
    KaliciOlayDeposu,
    KaliciOlayKaydi,
)



def test_kalici_olay_deposu():

    depo = KaliciOlayDeposu(
        "test_syk_arsiv"
    )


    kayit = KaliciOlayKaydi(
        "OLAY-039",
        [
            "KANIT-039"
        ],
        [
            "UZMAN-039"
        ],
        90,
        85,
    )


    depo.kaydet(
        kayit
    )


    assert (
        depo.mevcut_mu(
            "OLAY-039"
        )
        is True
    )


    sonuc = depo.yukle(
        "OLAY-039"
    )


    assert (
        sonuc.olay_kimligi
        ==
        "OLAY-039"
    )


    assert (
        len(
            sonuc.kanitlar
        )
        ==
        1
    )
