from syk_core.entegrasyon.guven_kalibrasyon_motoru import (
    GuvenKalibrasyonMotoru,
)



def test_guven_kalibrasyon():

    motor = GuvenKalibrasyonMotoru()


    sonuc = motor.hesapla(
        84.75,
        2,
        3,
        90,
    )


    assert (
        sonuc.toplam_guven
        ==
        100
    )


    assert (
        sonuc.karar
        ==
        "yuksek_dogrulama"
    )


def test_orta_destek():

    motor = GuvenKalibrasyonMotoru()


    sonuc = motor.hesapla(
        65,
        0,
        0,
        50,
    )


    assert (
        sonuc.karar
        ==
        "orta_destek"
    )
