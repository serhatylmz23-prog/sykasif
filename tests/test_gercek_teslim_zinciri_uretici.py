from syk_core.entegrasyon.gercek_teslim_zinciri_uretici import (
    GercekTeslimZinciriUretici,
)



def test_birlesik_teslim_zinciri():

    sistem = GercekTeslimZinciriUretici()


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        "a" * 64,

        "b" * 64,

        "c" * 64,

    )


    assert (
        sonuc.durum
        ==
        "birlesik_teslim_zinciri_hazir"
    )


    assert (
        sonuc.toplam_bilesen
        ==
        3
    )


    assert (
        len(
            sonuc.zincir_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True
