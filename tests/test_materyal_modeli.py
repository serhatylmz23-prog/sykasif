from syk_core.laboratuvar.materyal_modeli import (
    MateryalKaydi,
    MateryalLaboratuvarYoneticisi,
)


def test_materyal_kaydedilir():

    yonetici = MateryalLaboratuvarYoneticisi()

    kayit = yonetici.materyal_kaydet(
        MateryalKaydi(
            "MAT-001",
            "Bronz",
            "Ala??m",
        )
    )

    assert kayit.materyal_adi == "Bronz"



def test_laboratuvar_verileri_eklenir():

    yonetici = MateryalLaboratuvarYoneticisi()

    yonetici.materyal_kaydet(
        MateryalKaydi(
            "ALT-001",
            "Alt?n",
            "Metal",
        )
    )

    yonetici.veri_ekle(
        "ALT-001",
        "frekans_tepkileri",
        "?l??m-001",
    )

    yonetici.veri_ekle(
        "ALT-001",
        "derinlik_kayitlari",
        "5 cm",
    )

    kayit = yonetici.materyal_getir(
        "ALT-001"
    )

    assert len(
        kayit.frekans_tepkileri
    ) == 1

    assert len(
        kayit.derinlik_kayitlari
    ) == 1



def test_alasim_verisi_tutulur():

    yonetici = MateryalLaboratuvarYoneticisi()

    yonetici.materyal_kaydet(
        MateryalKaydi(
            "BRZ-001",
            "Arsenik Bronz",
            "Ala??m",
        )
    )

    yonetici.veri_ekle(
        "BRZ-001",
        "alasim_bilgileri",
        "bak?r arsenik oran?",
    )

    assert (
        len(
            yonetici.materyaller[
                "BRZ-001"
            ].alasim_bilgileri
        )
        == 1
    )
