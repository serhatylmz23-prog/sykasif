from syk_simulasyon.eylem_katmani import (
    BaglantiTuru, CihazProfili, CihazTuru, EylemIstegi, EylemTuru,
    KararSinifi, OneriVeEylemKatmani,
)
from syk_simulasyon.otonomi import BilgeKaanKontrolluOtonom, Karar, ParametreSiniri


def katman() -> OneriVeEylemKatmani:
    bilge = BilgeKaanKontrolluOtonom({
        "frekans_hz": ParametreSiniri("frekans_hz", 5000, 15000, "Hz"),
        "donus_yuzde": ParametreSiniri("donus_yuzde", -100, 100, "%"),
        "hiz_yuzde": ParametreSiniri("hiz_yuzde", 0, 100, "%"),
    })
    k = OneriVeEylemKatmani(bilge)
    k.cihaz_ekle(CihazProfili(
        "robot-1", CihazTuru.MINI_ROBOT,
        (BaglantiTuru.WIFI, BaglantiTuru.BLUETOOTH),
        (EylemTuru.SAGA_DON, EylemTuru.SOLA_DON, EylemTuru.GERI_CAGIR, EylemTuru.ACIL_DURDUR),
        adaptoru_var=True, bagli=True,
    ))
    k.cihaz_ekle(CihazProfili(
        "sensor-1", CihazTuru.SENSOR,
        (BaglantiTuru.KABLOLU,), (EylemTuru.FREKANS_DEGISTIR,),
        adaptoru_var=True, bagli=True,
    ))
    return k


def test_anlik_robot_yonlendirmesi_onaylanir():
    sonuc = katman().degerlendir(EylemIstegi("robot-1", EylemTuru.SAGA_DON, KararSinifi.ANLIK_EYLEM, {"donus_yuzde": 40}))
    assert sonuc.karar == Karar.ONAY and sonuc.uygulanabilir


def test_anlik_frekans_onayli_sinirda_degisebilir():
    sonuc = katman().degerlendir(EylemIstegi("sensor-1", EylemTuru.FREKANS_DEGISTIR, KararSinifi.ANLIK_EYLEM, {"frekans_hz": 9000}))
    assert sonuc.uygulanabilir


def test_frekans_sinir_disi_reddedilir():
    sonuc = katman().degerlendir(EylemIstegi("sensor-1", EylemTuru.FREKANS_DEGISTIR, KararSinifi.ANLIK_EYLEM, {"frekans_hz": 18000}))
    assert sonuc.karar == Karar.EK_VERI and not sonuc.uygulanabilir


def test_sistemsel_degisim_yalniz_oneri_olarak_kalir():
    sonuc = katman().degerlendir(EylemIstegi("sensor-1", EylemTuru.FREKANS_DEGISTIR, KararSinifi.SISTEMSEL_DEGISIKLIK, {"frekans_hz": 9000}))
    assert sonuc.karar == Karar.EK_VERI and not sonuc.uygulanabilir


def test_acil_durdurma_dogrudan_uygulanabilir():
    sonuc = katman().degerlendir(EylemIstegi("robot-1", EylemTuru.ACIL_DURDUR, KararSinifi.ANLIK_EYLEM))
    assert sonuc.uygulanabilir


def test_adaptorsuz_veya_baglantisiz_cihaz_otomatik_uyumlu_sayilmaz():
    k = katman()
    k.cihaz_ekle(CihazProfili("kamera-x", CihazTuru.YILAN_KAMERA, (BaglantiTuru.WIFI,), (EylemTuru.SAGA_DON,), False, True))
    sonuc = k.degerlendir(EylemIstegi("kamera-x", EylemTuru.SAGA_DON, KararSinifi.ANLIK_EYLEM, {"donus_yuzde": 20}))
    assert not sonuc.uygulanabilir
