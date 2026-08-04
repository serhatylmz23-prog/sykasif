from syk_core.entegrasyon.teslim_paketi_bagimsiz_dogrulama_motoru import (
    TeslimPaketiBagimsizDogrulamaMotoru,
)



def test_bagimsiz_dogrulama():

    sistem = TeslimPaketiBagimsizDogrulamaMotoru()


    sonuc = sistem.dogrula(

        "SYK-CORE-001",

        "a" * 64,

        "b" * 64,

        "c" * 64,

    )


    assert (
        sonuc.durum
        ==
        "bagimsiz_dogrulandi"
    )


    assert (
        sonuc.toplam_kontrol
        ==
        3
    )


    assert (
        sonuc.basarili_kontrol
        ==
        3
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
    )


    assert (
        len(
            sonuc.dogrulama_sha256
        )
        ==
        64
    )
