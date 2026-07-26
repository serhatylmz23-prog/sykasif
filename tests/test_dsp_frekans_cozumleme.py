import math
import pytest

from syk_simulasyon.dsp_frekans_cozumleme import (
    FrekansCozumleyici,
    PencereTuru,
    frekans_cozumle,
    pencere_katsayilari,
)


def sinyal_uret(frekans_hz, ornekleme_hz, n, genlik=1.0, dc=0.0):
    return tuple(
        dc + genlik * math.sin(2.0 * math.pi * frekans_hz * i / ornekleme_hz)
        for i in range(n)
    )


def test_dikdortgen_pencere_birdir():
    assert pencere_katsayilari(PencereTuru.DIKDORTGEN, 4) == (1.0, 1.0, 1.0, 1.0)


def test_hann_pencere_uclari_sifirdir():
    w = pencere_katsayilari(PencereTuru.HANN, 5)
    assert w[0] == pytest.approx(0.0)
    assert w[-1] == pytest.approx(0.0)
    assert w[2] == pytest.approx(1.0)


def test_hamming_pencere_simetriktir():
    w = pencere_katsayilari(PencereTuru.HAMMING, 11)
    assert w == pytest.approx(tuple(reversed(w)), abs=1e-12)


def test_tek_ornek_pencere_birdir():
    assert pencere_katsayilari(PencereTuru.HANN, 1) == (1.0,)


def test_sifir_ornek_pencere_reddedilir():
    with pytest.raises(ValueError):
        pencere_katsayilari(PencereTuru.HANN, 0)


def test_tek_frekans_dogru_tepeyi_verir():
    fs = 128.0
    n = 128
    x = sinyal_uret(16.0, fs, n)
    sonuc = frekans_cozumle(x, ornekleme_hz=fs, pencere=PencereTuru.DIKDORTGEN)
    assert sonuc.baskin_tepe is not None
    assert sonuc.baskin_tepe.frekans_hz == pytest.approx(16.0)
    assert sonuc.baskin_tepe.genlik == pytest.approx(1.0, abs=1e-12)


def test_iki_frekans_baskin_bileseni_bulur():
    fs = 256.0
    n = 256
    a = sinyal_uret(20.0, fs, n, genlik=0.4)
    b = sinyal_uret(50.0, fs, n, genlik=1.0)
    x = tuple(i + j for i, j in zip(a, b))
    sonuc = frekans_cozumle(x, ornekleme_hz=fs, pencere=PencereTuru.DIKDORTGEN)
    assert sonuc.baskin_tepe is not None
    assert sonuc.baskin_tepe.frekans_hz == pytest.approx(50.0)


def test_dc_genligi_ayri_raporlanir():
    fs = 64.0
    n = 64
    x = sinyal_uret(8.0, fs, n, genlik=1.0, dc=2.0)
    sonuc = frekans_cozumle(x, ornekleme_hz=fs, pencere=PencereTuru.DIKDORTGEN)
    assert sonuc.dc_genligi == pytest.approx(2.0, abs=1e-12)
    assert sonuc.baskin_tepe is not None
    assert sonuc.baskin_tepe.frekans_hz == pytest.approx(8.0)


def test_frekans_ekseni_ve_nyquist_dogru():
    sonuc = frekans_cozumle((0.0,) * 8, ornekleme_hz=80.0, pencere=PencereTuru.DIKDORTGEN)
    assert sonuc.frekans_hz == pytest.approx((0.0, 10.0, 20.0, 30.0, 40.0))
    assert sonuc.nyquist_hz == pytest.approx(40.0)
    assert sonuc.frekans_cozunurlugu_hz == pytest.approx(10.0)


def test_guc_genligin_karesidir():
    sonuc = frekans_cozumle(
        sinyal_uret(10.0, 100.0, 100),
        ornekleme_hz=100.0,
        pencere=PencereTuru.DIKDORTGEN,
    )
    assert sonuc.guc == pytest.approx(tuple(x * x for x in sonuc.genlik))


def test_ayni_girdi_ayni_cikti_verir():
    motor = FrekansCozumleyici()
    x = sinyal_uret(10.0, 100.0, 100)
    a = motor.coz(x, ornekleme_hz=100.0)
    b = motor.coz(x, ornekleme_hz=100.0)
    assert a == b


def test_yontem_ve_varsayimlar_kaydedilir():
    sonuc = frekans_cozumle((1.0, 0.0, -1.0, 0.0), ornekleme_hz=4.0)
    assert sonuc.yontem == "tek_tarafli_dft_referans"
    assert "sinyal_gercek_degerli" in sonuc.varsayimlar


@pytest.mark.parametrize("sinyal", [(), (math.nan,), (math.inf,), (-math.inf,)])
def test_gecersiz_sinyal_reddedilir(sinyal):
    with pytest.raises(ValueError):
        frekans_cozumle(sinyal, ornekleme_hz=100.0)


@pytest.mark.parametrize("fs", [0.0, -1.0, math.nan, math.inf])
def test_gecersiz_ornekleme_hizi_reddedilir(fs):
    with pytest.raises(ValueError):
        frekans_cozumle((1.0, 2.0), ornekleme_hz=fs)


def test_dc_haric_tepe_kapaliysa_dc_baskin_olabilir():
    sonuc = FrekansCozumleyici().coz(
        (5.0, 5.0, 5.0, 5.0),
        ornekleme_hz=4.0,
        pencere=PencereTuru.DIKDORTGEN,
        dc_haric_tepe=False,
    )
    assert sonuc.baskin_tepe is not None
    assert sonuc.baskin_tepe.frekans_hz == pytest.approx(0.0)
