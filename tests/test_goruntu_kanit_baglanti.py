from syk_core.goruntu.goruntu_kanit_baglanti import (
    GoruntuKaniti,
    GoruntuKanitYoneticisi,
)


def test_goruntu_kaniti_kaydedilir():

    yonetici = GoruntuKanitYoneticisi()

    kayit = yonetici.kaydet(
        GoruntuKaniti(
            "IMG-001",
            "video kaydi",
        )
    )

    assert kayit.kaynak_bilgisi == "video kaydi"



def test_manipulasyon_suphesi_tutulur():

    yonetici = GoruntuKanitYoneticisi()

    yonetici.kaydet(
        GoruntuKaniti(
            "VID-001",
            "dis kaynak",
        )
    )

    yonetici.suphe_ekle(
        "VID-001",
        "montaj supheli alan",
    )

    assert len(
        yonetici.kayitlar[
            "VID-001"
        ].manipulasyon_suphesi
    ) == 1



def test_goruntu_kanit_baglantisi():

    yonetici = GoruntuKanitYoneticisi()

    yonetici.kaydet(
        GoruntuKaniti(
            "FOTO-001",
            "saha fotografi",
        )
    )

    yonetici.nesne_adayi_ekle(
        "FOTO-001",
        "metal nesne",
    )

    yonetici.materyal_adayi_ekle(
        "FOTO-001",
        "bakir ihtimali",
    )

    yonetici.kanit_bagla(
        "FOTO-001",
        "KANIT-001",
    )

    kayit = yonetici.getir(
        "FOTO-001"
    )

    assert len(
        kayit.kanit_baglantilari
    ) == 1
