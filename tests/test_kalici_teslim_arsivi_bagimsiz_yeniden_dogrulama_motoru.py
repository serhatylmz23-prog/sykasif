from syk_core.entegrasyon.kalici_teslim_arsivi_bagimsiz_yeniden_dogrulama_motoru import (
    KaliciTeslimArsiviBagimsizYenidenDogrulamaMotoru,
)



def test_kalici_arsiv_bagimsiz_dogrulama():

    sistem = KaliciTeslimArsiviBagimsizYenidenDogrulamaMotoru()


    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        "a" * 64,

        "b" * 64,

        "c" * 64,

        "d" * 64,

    )


    assert (
        sonuc.durum
        ==
        "kalici_teslim_arsivi_bagimsiz_dogrulandi"
    )


    assert (
        sonuc.toplam_kontrol
        ==
        4
    )


    assert (
        sonuc.basarili_kontrol
        ==
        4
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
    )


    assert (
        len(
            sonuc.yeniden_dogrulama_sha256
        )
        ==
        64
    )
