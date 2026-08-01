from syk_core.degerlendirme.birlesik_degerlendirme import (
    BirlesikDegerlendirmeKaydi,
    BirlesikDegerlendirmeYoneticisi,
)


def test_birlesik_kayit_olusturulur():

    yonetici = BirlesikDegerlendirmeYoneticisi()

    kayit = yonetici.kaydet(
        BirlesikDegerlendirmeKaydi(
            "DEG-001"
        )
    )

    assert (
        kayit.degerlendirme_kimligi
        ==
        "DEG-001"
    )


def test_goruntu_ve_materyal_baglanir():

    yonetici = BirlesikDegerlendirmeYoneticisi()

    yonetici.kaydet(
        BirlesikDegerlendirmeKaydi(
            "DEG-002"
        )
    )

    yonetici.goruntu_ekle(
        "DEG-002",
        "goruntu kaniti",
    )

    yonetici.materyal_ekle(
        "DEG-002",
        "altin aday analizi",
    )

    kayit = yonetici.getir(
        "DEG-002"
    )

    assert len(
        kayit.goruntu_kaniti
    ) == 1

    assert len(
        kayit.materyal_analizi
    ) == 1


def test_guven_celiski_uzman_bilgisi():

    yonetici = BirlesikDegerlendirmeYoneticisi()

    yonetici.kaydet(
        BirlesikDegerlendirmeKaydi(
            "DEG-003"
        )
    )

    yonetici.guven_puani_ver(
        "DEG-003",
        85.0,
    )

    yonetici.celiski_ekle(
        "DEG-003",
        "konum eksik",
    )

    yonetici.uzman_yorumu_ekle(
        "DEG-003",
        "ek inceleme gerekli",
    )

    yonetici.degerlendirme_tamamla(
        "DEG-003"
    )

    kayit = yonetici.getir(
        "DEG-003"
    )

    assert kayit.durum == "incelendi"
    assert kayit.kaynak_guven_puani == 85.0
