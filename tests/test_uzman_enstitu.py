from syk_core.uzmanlar.uzman_enstitu import (
    UzmanBaglantisi,
    UzmanEnstituAgaci,
    UzmanEnstitusu,
    UzmanErisimYasagi,
)


def test_uzman_ailesine_bagli_olur():

    agac = UzmanEnstituAgaci()

    agac.enstitu_ekle(
        UzmanEnstitusu(
            "JEO",
            "Yer Bilimleri Enstitusu",
            "Jeoloji",
        )
    )

    agac.uzman_ekle(
        UzmanBaglantisi(
            "JEO-001",
            "Jeoloji Uzmani",
            "JEO",
        )
    )

    assert (
        "JEO-001"
        in agac.enstituler["JEO"].uzmanlar
    )


def test_farkli_aile_verisine_erisim_yoktur():

    agac = UzmanEnstituAgaci()

    agac.enstitu_ekle(
        UzmanEnstitusu(
            "JEO",
            "Jeoloji",
            "Yer",
        )
    )

    agac.enstitu_ekle(
        UzmanEnstitusu(
            "GOR",
            "Goruntu",
            "Goruntu",
        )
    )

    agac.uzman_ekle(
        UzmanBaglantisi(
            "JEO-001",
            "Jeoloji",
            "JEO",
        )
    )

    agac.uzman_ekle(
        UzmanBaglantisi(
            "GOR-001",
            "Goruntu",
            "GOR",
        )
    )

    try:
        agac.veri_gorme_izni(
            "JEO-001",
            "GOR-001",
        )
        assert False

    except UzmanErisimYasagi:
        assert True


def test_uzman_emekliye_ayrilir():

    agac = UzmanEnstituAgaci()

    agac.enstitu_ekle(
        UzmanEnstitusu(
            "SON",
            "Sonar",
            "Akustik",
        )
    )

    agac.uzman_ekle(
        UzmanBaglantisi(
            "SON-001",
            "Sonar Uzmani",
            "SON",
        )
    )

    agac.emekliye_ayir(
        "SON-001"
    )

    assert agac.uzmanlar[
        "SON-001"
    ].emekli
