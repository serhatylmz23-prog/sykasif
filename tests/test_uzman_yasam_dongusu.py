from syk_core.uzmanlar.uzman_yasam_dongusu import (
    UzmanYasamKaydi,
    UzmanYasamYoneticisi,
)


def test_uzman_olusturulur():

    yonetici = UzmanYasamYoneticisi()

    uzman = yonetici.uzman_olustur(
        UzmanYasamKaydi(
            "GOR-001",
            "Goruntu Uzmani",
            "Goruntu",
        )
    )

    assert uzman.durum == "aktif"



def test_uzman_egitim_ve_deneyim_kaydi():

    yonetici = UzmanYasamYoneticisi()

    yonetici.uzman_olustur(
        UzmanYasamKaydi(
            "JEO-001",
            "Jeoloji Uzmani",
            "Yer Bilimleri",
        )
    )

    yonetici.egitim_ekle(
        "JEO-001",
        "yeni analiz modeli",
    )

    yonetici.deneyim_ekle(
        "JEO-001",
        "saha deneyimi",
    )

    uzman = yonetici.uzmanlar[
        "JEO-001"
    ]

    assert len(
        uzman.egitim_kaydi
    ) == 1

    assert len(
        uzman.deneyim_kaydi
    ) == 1



def test_eski_uzman_yeni_uzmana_bilgi_aktarir():

    yonetici = UzmanYasamYoneticisi()

    yonetici.uzman_olustur(
        UzmanYasamKaydi(
            "SON-001",
            "Eski Sonar Uzmani",
            "Sonar",
        )
    )

    yonetici.uzman_olustur(
        UzmanYasamKaydi(
            "SON-002",
            "Yeni Sonar Uzmani",
            "Sonar",
        )
    )

    yonetici.bilgiyi_aktar(
        "SON-001",
        "SON-002",
        "eski sonar tecrubesi",
    )

    assert (
        len(
            yonetici.uzmanlar[
                "SON-002"
            ].aktarilan_bilgi
        )
        ==
        1
    )



def test_uzman_emekliye_ayrilir():

    yonetici = UzmanYasamYoneticisi()

    yonetici.uzman_olustur(
        UzmanYasamKaydi(
            "FIN-001",
            "Finans Uzmani",
            "Finans",
        )
    )

    yonetici.emekliye_ayir(
        "FIN-001"
    )

    assert not yonetici.aktif_mi(
        "FIN-001"
    )
