from syk_core.degerlendirme.konsensus_motoru import (
    KonsensusKaydi,
    KonsensusMotoru,
)



def test_konsensus_kaydi():

    motor = KonsensusMotoru()

    kayit = motor.kaydet(
        KonsensusKaydi(
            "KON-001",
            kaynak_guven_puani=70,
        )
    )

    assert (
        kayit.degerlendirme_kimligi
        ==
        "KON-001"
    )



def test_uzman_destegi_puani_artirir():

    motor = KonsensusMotoru()

    motor.kaydet(
        KonsensusKaydi(
            "KON-002",
            kaynak_guven_puani=70,
        )
    )

    motor.uzman_destek_ekle(
        "KON-002",
        "uyumlu analiz",
    )

    sonuc = motor.hesapla(
        "KON-002"
    )

    assert sonuc.konsensus_puani == 80
    assert sonuc.durum == "guclu_destek"



def test_celiski_guveni_dusurur():

    motor = KonsensusMotoru()

    motor.kaydet(
        KonsensusKaydi(
            "KON-003",
            kaynak_guven_puani=80,
        )
    )

    motor.celiski_ekle(
        "KON-003"
    )

    sonuc = motor.hesapla(
        "KON-003"
    )

    assert sonuc.konsensus_puani == 75
    assert sonuc.durum == "inceleme_gerekli"
