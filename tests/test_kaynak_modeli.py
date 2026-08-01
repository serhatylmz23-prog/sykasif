from syk_core.kanit.kaynak_modeli import (
    KaynakKaydi,
    KanitKaynakYoneticisi,
)


def test_kaynak_eklenir():

    yonetici = KanitKaynakYoneticisi()

    kaynak = yonetici.kaynak_ekle(
        KaynakKaydi(
            "AKD-001",
            "Akademik yayin",
            "universite makalesi",
        )
    )

    assert (
        kaynak.kaynak_turu
        ==
        "Akademik yayin"
    )


def test_guven_puani_guncellenir():

    yonetici = KanitKaynakYoneticisi()

    yonetici.kaynak_ekle(
        KaynakKaydi(
            "PAT-001",
            "Patent",
            "malzeme arastirmasi",
        )
    )

    yonetici.guven_puani_guncelle(
        "PAT-001",
        92.5,
    )

    assert (
        yonetici.kaynaklar[
            "PAT-001"
        ].guven_puani
        ==
        92.5
    )


def test_celiski_ve_uzman_notu_kaydedilir():

    yonetici = KanitKaynakYoneticisi()

    yonetici.kaynak_ekle(
        KaynakKaydi(
            "GOR-001",
            "Goruntu/video",
            "saha videosu",
        )
    )

    yonetici.celiski_ekle(
        "GOR-001",
        "konum bilgisi eksik",
    )

    yonetici.uzman_notu_ekle(
        "GOR-001",
        "goruntu inceleme gerekli",
    )

    kaynak = yonetici.kaynaklar[
        "GOR-001"
    ]

    assert len(
        kaynak.celiski_kayitlari
    ) == 1

    assert len(
        kaynak.uzman_notlari
    ) == 1
