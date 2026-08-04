from syk_core.entegrasyon.sha256_kapanis_paketi_uretici import (
    SHA256KapanisPaketiUretici,
)



def test_sha256_kapanis():

    sistem = SHA256KapanisPaketiUretici()


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        "a" * 64,

        "b" * 64,

        "c" * 64,

    )


    assert (
        sonuc.durum
        ==
        "son_arsiv_kapanis_hazir"
    )


    assert (
        sonuc.toplam_bilesen
        ==
        3
    )


    assert (
        len(
            sonuc.kapanis_hash
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True
