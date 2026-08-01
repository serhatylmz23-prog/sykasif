from syk_core.kanit.kaynak_tarama_modeli import (
    KaynakTarama,
    KaynakTaramaYoneticisi,
)


def test_kaynak_tarama_eklenir():

    yonetici = KaynakTaramaYoneticisi()

    kaynak = yonetici.kaynak_ekle(
        KaynakTarama(
            "AKD-001",
            "Akademik",
            "universite tezi",
        )
    )

    assert kaynak.kaynak_turu == "Akademik"



def test_ogrenme_havuzu_veri_tutar():

    yonetici = KaynakTaramaYoneticisi()

    yonetici.kaynak_ekle(
        KaynakTarama(
            "PAT-001",
            "Patent",
            "malzeme patenti",
        )
    )

    yonetici.veri_ekle(
        "PAT-001",
        "ala?im bilgisi",
    )

    assert len(
        yonetici.kaynak_getir(
            "PAT-001"
        ).ogrenilen_veriler
    ) == 1



def test_kaynak_analizi_tamamlanir():

    yonetici = KaynakTaramaYoneticisi()

    yonetici.kaynak_ekle(
        KaynakTarama(
            "MUZ-001",
            "M?ze",
            "eser kaydi",
        )
    )

    yonetici.analiz_tamamla(
        "MUZ-001"
    )

    assert (
        yonetici.kaynak_getir(
            "MUZ-001"
        ).analiz_durumu
        ==
        "tamamlandi"
    )
