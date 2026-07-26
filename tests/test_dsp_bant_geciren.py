import math
import pytest

from syk_simulasyon.dsp_bant_geciren import (
    BantGecirenAyar,
    BantGecirenSuzgec,
    bant_gecir,
)


def sinyal_uret(frekans_hz, ornekleme_hz, sure_s, genlik=1.0):
    n = int(ornekleme_hz * sure_s)
    return tuple(
        genlik * math.sin(2.0 * math.pi * frekans_hz * i / ornekleme_hz)
        for i in range(n)
    )


def rms(dizi):
    return math.sqrt(sum(x * x for x in dizi) / len(dizi))


def test_ayar_dogrulama_gecerli():
    BantGecirenAyar(10.0, 20.0, 100.0, 101).dogrula()


@pytest.mark.parametrize("alt,ust,fs", [
    (0.0, 20.0, 100.0),
    (20.0, 10.0, 100.0),
    (10.0, 50.0, 100.0),
    (10.0, 60.0, 100.0),
    (10.0, 20.0, 0.0),
])
def test_gecersiz_kesim_frekanslari_reddedilir(alt, ust, fs):
    with pytest.raises(ValueError):
        BantGecirenAyar(alt, ust, fs, 101).dogrula()


def test_cift_sira_reddedilir():
    with pytest.raises(ValueError):
        BantGecirenAyar(10.0, 20.0, 100.0, 100).dogrula()


def test_cok_kucuk_sira_reddedilir():
    with pytest.raises(ValueError):
        BantGecirenAyar(10.0, 20.0, 100.0, 1).dogrula()


def test_sira_tam_sayi_olmali():
    with pytest.raises(TypeError):
        BantGecirenAyar(10.0, 20.0, 100.0, 101.5).dogrula()


def test_katsayilar_simetriktir():
    h = BantGecirenSuzgec().katsayi_uret(BantGecirenAyar(10.0, 20.0, 100.0, 101))
    assert h == pytest.approx(tuple(reversed(h)), abs=1e-12)


def test_katsayi_sayisi_siraya_esittir():
    h = BantGecirenSuzgec().katsayi_uret(BantGecirenAyar(10.0, 20.0, 100.0, 51))
    assert len(h) == 51


def test_gecis_bandindaki_sinyal_buyuk_oranda_korunur():
    fs = 200.0
    x = sinyal_uret(30.0, fs, 3.0)
    y = bant_gecir(x, alt_kesim_hz=20.0, ust_kesim_hz=40.0, ornekleme_hz=fs, sira=101)
    orta = y[100:-100]
    assert rms(orta) > 0.55


def test_alt_durdurma_bandindaki_sinyal_bastirilir():
    fs = 200.0
    x = sinyal_uret(5.0, fs, 3.0)
    y = bant_gecir(x, alt_kesim_hz=20.0, ust_kesim_hz=40.0, ornekleme_hz=fs, sira=101)
    orta = y[100:-100]
    assert rms(orta) < 0.08


def test_ust_durdurma_bandindaki_sinyal_bastirilir():
    fs = 200.0
    x = sinyal_uret(70.0, fs, 3.0)
    y = bant_gecir(x, alt_kesim_hz=20.0, ust_kesim_hz=40.0, ornekleme_hz=fs, sira=101)
    orta = y[100:-100]
    assert rms(orta) < 0.08


def test_karma_sinyalde_gecis_bandi_bileseni_kalir():
    fs = 200.0
    a = sinyal_uret(30.0, fs, 3.0)
    b = sinyal_uret(5.0, fs, 3.0, genlik=0.8)
    c = sinyal_uret(70.0, fs, 3.0, genlik=0.8)
    x = tuple(i + j + k for i, j, k in zip(a, b, c))
    y = bant_gecir(x, alt_kesim_hz=20.0, ust_kesim_hz=40.0, ornekleme_hz=fs, sira=101)
    orta = y[100:-100]
    assert 0.55 < rms(orta) < 0.85


def test_cikti_uzunlugu_korunur():
    x = (1.0, 2.0, 3.0, 4.0)
    y = bant_gecir(x, alt_kesim_hz=10.0, ust_kesim_hz=20.0, ornekleme_hz=100.0, sira=5)
    assert len(y) == len(x)


def test_ayni_girdi_ayni_cikti_verir():
    motor = BantGecirenSuzgec()
    ayar = BantGecirenAyar(10.0, 20.0, 100.0, 21)
    x = tuple(float(i) for i in range(50))
    assert motor.uygula(x, ayar) == motor.uygula(x, ayar)


def test_grup_gecikmesi_dogru_kaydedilir():
    sonuc = BantGecirenSuzgec().uygula(
        tuple(float(i) for i in range(50)),
        BantGecirenAyar(10.0, 20.0, 100.0, 21),
    )
    assert sonuc.grup_gecikmesi_ornek == 10


def test_yontem_ve_varsayimlar_kaydedilir():
    sonuc = BantGecirenSuzgec().uygula(
        tuple(float(i) for i in range(50)),
        BantGecirenAyar(10.0, 20.0, 100.0, 21),
    )
    assert sonuc.yontem == "fir_pencerelenmis_sinc_hamming"
    assert "kenar_ornekleri_sifir_dolguyla_islenir" in sonuc.varsayimlar


@pytest.mark.parametrize("sinyal", [(), (math.nan,), (math.inf,), (-math.inf,)])
def test_gecersiz_sinyal_reddedilir(sinyal):
    with pytest.raises(ValueError):
        bant_gecir(
            sinyal,
            alt_kesim_hz=10.0,
            ust_kesim_hz=20.0,
            ornekleme_hz=100.0,
            sira=21,
        )
