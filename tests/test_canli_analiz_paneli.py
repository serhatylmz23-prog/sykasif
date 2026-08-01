from syk_core.goruntu.canli_analiz_paneli import (
    CanliGoruntuAkisi,
    CanliAnalizPaneli,
)


def test_canli_akis_baslatilir():

    panel = CanliAnalizPaneli()

    akis = panel.akis_baslat(
        CanliGoruntuAkisi(
            "DRONE-001",
            "kamera",
        )
    )

    assert akis.aktif



def test_anlik_kare_kaydi():

    panel = CanliAnalizPaneli()

    panel.akis_baslat(
        CanliGoruntuAkisi(
            "CAM-001",
            "yilan_kamera",
        )
    )

    panel.kare_kaydet(
        "CAM-001",
        "tas duvar inceleme karesi",
    )

    assert (
        panel.akislar[
            "CAM-001"
        ].kare_sayisi
        ==
        1
    )



def test_supheli_alan_aktarilir():

    panel = CanliAnalizPaneli()

    panel.akis_baslat(
        CanliGoruntuAkisi(
            "DRN-001",
            "drone",
        )
    )

    panel.supheli_alan_bildir(
        "DRN-001",
        "yapida farkli doku",
    )

    durum = panel.analiz_durumu(
        "DRN-001"
    )

    assert durum["supheli_alan"] == 1



def test_akis_durdurulur():

    panel = CanliAnalizPaneli()

    panel.akis_baslat(
        CanliGoruntuAkisi(
            "CAM-002",
            "kamera",
        )
    )

    panel.durdur(
        "CAM-002"
    )

    assert not panel.akislar[
        "CAM-002"
    ].aktif
