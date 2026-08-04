from syk_core.entegrasyon.tam_cekirdek_dogrulama_raporu import (
    TamCekirdekDogrulamaRaporuUretici,
)



def test_tam_cekirdek_dogrulama():

    sistem = TamCekirdekDogrulamaRaporuUretici()


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        [
            "SPRINT-054",
            "SPRINT-055",
            "SPRINT-056",
            "SPRINT-057",
            "SPRINT-058",
            "SPRINT-059",
            "SPRINT-060",
            "SPRINT-061",
            "SPRINT-062",
            "SPRINT-063",
            "SPRINT-064",
            "SPRINT-065",
            "SPRINT-066",
            "SPRINT-067",
            "SPRINT-068",
        ],

        [
            "HASH",
            "KANIT",
            "MANIFEST",
            "MUHUR",
            "DEVIR",
            "ARTEFAKT",
        ],

        [
            "kaynak_kod",
            "test_kod",
            "manifest",
        ],

        {
            "SHA":
                True,

            "MANIFEST":
                True,

            "MUHUR":
                True,

            "KANIT":
                True,

        },

    )


    assert (
        sonuc.durum
        ==
        "tam_dogrulandi"
    )


    assert (
        sonuc.sprint_sayisi
        ==
        15
    )


    assert (
        sonuc.modul_sayisi
        ==
        6
    )


    assert (
        sonuc.artefakt_sayisi
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
            sonuc.rapor_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc,
        [
            "SPRINT-054",
            "SPRINT-055",
            "SPRINT-056",
            "SPRINT-057",
            "SPRINT-058",
            "SPRINT-059",
            "SPRINT-060",
            "SPRINT-061",
            "SPRINT-062",
            "SPRINT-063",
            "SPRINT-064",
            "SPRINT-065",
            "SPRINT-066",
            "SPRINT-067",
            "SPRINT-068",
        ],
        [
            "HASH",
            "KANIT",
            "MANIFEST",
            "MUHUR",
            "DEVIR",
            "ARTEFAKT",
        ],
        [
            "kaynak_kod",
            "test_kod",
            "manifest",
        ],
        {
            "SHA": True,
            "MANIFEST": True,
            "MUHUR": True,
            "KANIT": True,
        },
    ) is True
