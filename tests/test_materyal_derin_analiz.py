from syk_core.laboratuvar.materyal_derin_analiz import (
    DerinlikAnalizi,
    MateryalDerinAnaliz,
    MateryalDerinAnalizYoneticisi,
)


def test_derin_analiz_kaydi():

    yonetici = MateryalDerinAnalizYoneticisi()

    yonetici.kaydet(
        MateryalDerinAnaliz(
            "ALT-001"
        )
    )

    yonetici.derinlik_kaydi_ekle(
        "ALT-001",
        DerinlikAnalizi(
            5
        )
    )

    assert (
        len(
            yonetici.getir(
                "ALT-001"
            ).derinlik_analizleri
        )
        == 1
    )


def test_fizik_kimya_verisi():

    yonetici = MateryalDerinAnalizYoneticisi()

    yonetici.kaydet(
        MateryalDerinAnaliz(
            "BRZ-001"
        )
    )

    yonetici.veri_ekle(
        "BRZ-001",
        "element_verileri",
        "bakir arsenik oranlari",
    )

    yonetici.veri_ekle(
        "BRZ-001",
        "kimyasal_ozellikler",
        "ala?im analizi",
    )

    kayit = yonetici.getir(
        "BRZ-001"
    )

    assert len(
        kayit.element_verileri
    ) == 1


def test_sensor_ve_frekans_kaydi():

    analiz = DerinlikAnalizi(
        10
    )

    analiz.frekans_tepkisi.append(
        "ornek frekans"
    )

    analiz.sensor_kayitlari.append(
        "sonar veri"
    )

    assert len(
        analiz.sensor_kayitlari
    ) == 1
