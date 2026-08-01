from syk_core.kanit.kaynak_turleri import (
    KaynakTuru,
    KaynakTurYonetici,
)


def test_kaynak_turu_eklenir():

    yonetici = KaynakTurYonetici()

    yonetici.tur_ekle(
        KaynakTuru(
            "AKD",
            "Akademik Kaynak",
            "makale tez arastirma",
        )
    )

    assert (
        "AKD"
        in yonetici.turler
    )


def test_alt_kaynaklar_tutulur():

    yonetici = KaynakTurYonetici()

    yonetici.tur_ekle(
        KaynakTuru(
            "MED",
            "Medya",
            "video sosyal medya forum",
        )
    )

    yonetici.alt_kaynak_ekle(
        "MED",
        "YouTube",
    )

    yonetici.alt_kaynak_ekle(
        "MED",
        "Forum",
    )

    assert len(
        yonetici.turler["MED"].alt_kaynaklar
    ) == 2


def test_aktif_kaynaklar_getirilir():

    yonetici = KaynakTurYonetici()

    yonetici.tur_ekle(
        KaynakTuru(
            "PAT",
            "Patent",
            "patent verileri",
        )
    )

    assert len(
        yonetici.aktif_turleri_getir()
    ) == 1
