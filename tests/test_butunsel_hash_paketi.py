from syk_core.entegrasyon.butunsel_hash_paketi import (
    ButunselHashPaketi,
)



def test_butunsel_hash_paketi():

    sistem = ButunselHashPaketi()


    sistem.paket_olustur(
        "OLAY-037",
        [
            "KANIT-A",
        ],
        [
            "UZMAN-A",
        ],
        90,
        85,
    )


    assert (
        sistem.dogrula(
            "OLAY-037",
            [
                "KANIT-A",
            ],
            [
                "UZMAN-A",
            ],
            90,
            85,
        )
        is True
    )


    assert (
        sistem.dogrula(
            "OLAY-037",
            [
                "KANIT-DEGISIK",
            ],
            [
                "UZMAN-A",
            ],
            90,
            85,
        )
        is False
    )


    kayit = sistem.getir(
        "OLAY-037"
    )


    assert (
        len(
            kayit.paket_hashi
        )
        ==
        64
    )
