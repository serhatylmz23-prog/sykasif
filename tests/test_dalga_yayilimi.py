import math
import pytest

from syk_simulasyon.dalga_denklemleri import db_genlik_katsayisi, gidis_donus_gecikmesi_s
from syk_simulasyon.dalga_yayilimi import DalgaYayilimGirdisi, DalgaYayilimMotoru
from syk_simulasyon.ortam_modeli import OrtamModeli


def ortam(zayiflama=0.0):
    return OrtamModeli("su", yayilim_hizi_m_s=1500.0, zayiflama_db_m=zayiflama)


def girdi(**degisiklik):
    veri = dict(
        ortam=ortam(),
        derinlik_m=1.0,
        frekans_hz=1000.0,
        ornekleme_hz=10000.0,
        sure_s=0.01,
        baslangic_genligi=1.0,
        yansima_katsayisi=1.0,
        gurultu_std=0.0,
        rastgele_tohum=7,
    )
    veri.update(degisiklik)
    return DalgaYayilimGirdisi(**veri)


def test_gecikme_hesabi():
    assert gidis_donus_gecikmesi_s(1.5, 1500.0) == pytest.approx(0.002)


def test_sifir_db_zayiflama_birdir():
    assert db_genlik_katsayisi(0.0, 99.0) == pytest.approx(1.0)


def test_20_db_zayiflama_onda_birdir():
    assert db_genlik_katsayisi(10.0, 2.0) == pytest.approx(0.1)


def test_uretim_ornek_sayisi():
    sonuc = DalgaYayilimMotoru().uret(girdi())
    assert len(sonuc.zaman_s) == 100
    assert len(sonuc.genlik) == 100


def test_gecikmeden_once_sinyal_yok():
    sonuc = DalgaYayilimMotoru().uret(girdi())
    gecikme_ornegi = int(math.ceil(sonuc.gecikme_s * 10000.0))
    assert all(x == 0.0 for x in sonuc.genlik[:gecikme_ornegi])


def test_ayni_girdi_ayni_cikti():
    motor = DalgaYayilimMotoru()
    a = motor.uret(girdi(gurultu_std=0.1, rastgele_tohum=42))
    b = motor.uret(girdi(gurultu_std=0.1, rastgele_tohum=42))
    assert a == b


def test_farkli_tohum_farkli_gurultu():
    motor = DalgaYayilimMotoru()
    a = motor.uret(girdi(gurultu_std=0.1, rastgele_tohum=1))
    b = motor.uret(girdi(gurultu_std=0.1, rastgele_tohum=2))
    assert a.genlik != b.genlik


def test_derinlik_arttikca_gecikme_artar():
    motor = DalgaYayilimMotoru()
    a = motor.uret(girdi(derinlik_m=0.5))
    b = motor.uret(girdi(derinlik_m=2.0))
    assert b.gecikme_s > a.gecikme_s


def test_zayiflama_tepe_genligi_dusurur():
    motor = DalgaYayilimMotoru()
    a = motor.uret(girdi(ortam=ortam(0.0)))
    b = motor.uret(girdi(ortam=ortam(10.0)))
    assert max(map(abs, b.genlik)) < max(map(abs, a.genlik))


@pytest.mark.parametrize("derinlik", [-0.01, 2.26])
def test_gecersiz_derinlik_reddedilir(derinlik):
    with pytest.raises(ValueError):
        DalgaYayilimMotoru().uret(girdi(derinlik_m=derinlik))


def test_nyquist_siniri_reddedilir():
    with pytest.raises(ValueError):
        DalgaYayilimMotoru().uret(girdi(frekans_hz=6000.0, ornekleme_hz=10000.0))


def test_gecersiz_yansima_katsayisi_reddedilir():
    with pytest.raises(ValueError):
        DalgaYayilimMotoru().uret(girdi(yansima_katsayisi=1.1))


def test_varsayimlar_ciktiya_yazilir():
    sonuc = DalgaYayilimMotoru().uret(girdi())
    assert "homojen_ortam" in sonuc.kullanılan_varsayimlar
    assert "tek_yansima" in sonuc.kullanılan_varsayimlar
