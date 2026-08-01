from syk_core.kanit.guven_motoru import (
    DegerlendirmeKaydi,
    GuvenHesapMotoru,
)


def test_guven_puani_hesaplanir():

    motor = GuvenHesapMotoru()

    sonuc = motor.guven_hesapla(
        DegerlendirmeKaydi(
            "MAT-001",
            kaynak_sayisi=5,
            destekleyen_bulgu=8,
            celiski_sayisi=0,
        )
    )

    assert sonuc > 0



def test_celiski_puani_dusurur():

    motor = GuvenHesapMotoru()

    sonuc = motor.guven_hesapla(
        DegerlendirmeKaydi(
            "GOR-001",
            kaynak_sayisi=5,
            destekleyen_bulgu=5,
            celiski_sayisi=3,
        )
    )

    assert sonuc < 60



def test_celiski_kaydi_isaretlenir():

    motor = GuvenHesapMotoru()

    sonuc = motor.celiski_degerlendir(
        DegerlendirmeKaydi(
            "VID-001",
            celiski_sayisi=1,
        )
    )

    assert sonuc["celiski_var"]
    assert sonuc["incelenmeli"]
