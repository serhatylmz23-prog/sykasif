from syk_core.entegrasyon.kanit_sha256_dogrulama import (
    KanitSHA256Dogrulama,
)



def test_kanit_sha256_zinciri():

    sistem = KanitSHA256Dogrulama()


    sistem.kaydet(
        "KANIT-036",
        "ALTIN-VERISI",
    )


    assert (
        sistem.dogrula(
            "KANIT-036",
            "ALTIN-VERISI",
        )
        is True
    )


    assert (
        sistem.dogrula(
            "KANIT-036",
            "DEGISMIS-VERI",
        )
        is False
    )


    kayit = sistem.getir(
        "KANIT-036"
    )


    assert (
        len(
            kayit.veri_hashi
        )
        ==
        64
    )
