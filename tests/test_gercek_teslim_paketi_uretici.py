from syk_core.entegrasyon.gercek_teslim_paketi_uretici import (
    GercekTeslimPaketiUretici,
)



def test_gercek_teslim_paketi():

    sistem = GercekTeslimPaketiUretici()


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        "a" * 64,

        "b" * 64,

        "c" * 64,

    )


    assert (
        sonuc.durum
        ==
        "gercek_teslim_paketi_hazir"
    )


    assert (
        sonuc.toplam_bilesen
        ==
        3
    )


    assert (
        len(
            sonuc.paket_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True
