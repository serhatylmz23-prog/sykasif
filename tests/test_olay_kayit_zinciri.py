from syk_core.entegrasyon.olay_kayit_zinciri import (
    OlayKayitZinciri,
)



def test_olay_kayit_zinciri():

    zincir = OlayKayitZinciri()


    zincir.kaydet(
        "OLAY-035"
    )


    zincir.kanit_ekle(
        "OLAY-035",
        "KANIT-035",
    )


    zincir.uzman_sonucu_ekle(
        "OLAY-035",
        "UZMAN-SONUC",
    )


    zincir.puan_kaydet(
        "OLAY-035",
        90,
        90,
    )


    assert (
        zincir.dogrula(
            "OLAY-035"
        )
        is True
    )


    sonuc = zincir.getir(
        "OLAY-035"
    )


    assert (
        len(
            sonuc.kanitlar
        )
        ==
        1
    )


    assert (
        len(
            sonuc.uzman_sonuclari
        )
        ==
        1
    )


    assert (
        sonuc.guven_puani
        ==
        90
    )
