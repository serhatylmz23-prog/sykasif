import math
import pytest

from syk_simulasyon.dsp_dc_kayma import (
    DCKaymaGiderici,
    dc_kaymayi_gider,
)


def test_sabit_kayma_tamamen_giderilir():
    sonuc = DCKaymaGiderici().uygula((5.0, 5.0, 5.0, 5.0))
    assert sonuc.cikti == pytest.approx((0.0, 0.0, 0.0, 0.0))
    assert sonuc.hesaplanan_kayma == pytest.approx(5.0)
    assert sonuc.cikti_ortalamasi == pytest.approx(0.0)


def test_sinyal_bicimi_korunur():
    sonuc = DCKaymaGiderici().uygula((2.0, 3.0, 4.0))
    assert sonuc.cikti == pytest.approx((-1.0, 0.0, 1.0))
    assert sonuc.ornek_sayisi == 3


def test_negatif_kayma_giderilir():
    sonuc = DCKaymaGiderici().uygula((-3.0, -2.0, -1.0))
    assert sonuc.hesaplanan_kayma == pytest.approx(-2.0)
    assert sonuc.cikti == pytest.approx((-1.0, 0.0, 1.0))


def test_referans_araligi_ile_kayma_hesaplanir():
    sonuc = DCKaymaGiderici().uygula(
        (10.0, 10.0, 12.0, 14.0),
        referans_baslangic=0,
        referans_bitis=2,
    )
    assert sonuc.hesaplanan_kayma == pytest.approx(10.0)
    assert sonuc.cikti == pytest.approx((0.0, 0.0, 2.0, 4.0))


def test_referans_araligi_tum_ciktinin_ortalamasini_sifirlamak_zorunda_degildir():
    sonuc = DCKaymaGiderici().uygula(
        (1.0, 1.0, 4.0),
        referans_baslangic=0,
        referans_bitis=2,
    )
    assert sonuc.cikti_ortalamasi == pytest.approx(1.0)


def test_kolay_kullanim_fonksiyonu():
    assert dc_kaymayi_gider((1.0, 2.0, 3.0)) == pytest.approx((-1.0, 0.0, 1.0))


def test_ayni_girdi_ayni_cikti_verir():
    motor = DCKaymaGiderici()
    a = motor.uygula((0.1, 0.2, 0.3))
    b = motor.uygula((0.1, 0.2, 0.3))
    assert a == b


def test_yontem_ve_varsayimlar_kaydedilir():
    sonuc = DCKaymaGiderici().uygula((1.0, 2.0))
    assert sonuc.yontem == "aritmetik_ortalama_cikarma"
    assert "kayma_sabit_kabul_edildi" in sonuc.varsayimlar


@pytest.mark.parametrize("sinyal", [(), (math.nan,), (math.inf,), (-math.inf,)])
def test_gecersiz_sinyal_reddedilir(sinyal):
    with pytest.raises(ValueError):
        DCKaymaGiderici().uygula(sinyal)


@pytest.mark.parametrize("baslangic,bitis", [
    (-1, 2),
    (0, 0),
    (2, 1),
    (0, 4),
])
def test_gecersiz_referans_araligi_reddedilir(baslangic, bitis):
    with pytest.raises(ValueError):
        DCKaymaGiderici().uygula(
            (1.0, 2.0, 3.0),
            referans_baslangic=baslangic,
            referans_bitis=bitis,
        )


def test_referans_siniri_tam_sayi_olmali():
    with pytest.raises(TypeError):
        DCKaymaGiderici().uygula(
            (1.0, 2.0, 3.0),
            referans_baslangic=0.5,
            referans_bitis=2,
        )
