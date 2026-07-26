import pytest

from syk_simulasyon.zayiflama_modeli import ZayiflamaGirdisi, ZayiflamaModeli
from syk_simulasyon.dalga_yayilimi import DalgaYayilimGirdisi, DalgaYayilimMotoru
from syk_simulasyon.ortam_modeli import OrtamModeli


def test_gidis_donus_yolu_iki_katidir():
    s = ZayiflamaModeli().hesapla(ZayiflamaGirdisi(1.5, 2.0))
    assert s.toplam_yol_m == pytest.approx(3.0)
    assert s.ortam_kaybi_db == pytest.approx(6.0)


def test_20_db_toplam_kayip_genligi_onda_bire_indirir():
    s = ZayiflamaModeli().hesapla(ZayiflamaGirdisi(1.0, 10.0))
    assert s.toplam_kayip_db == pytest.approx(20.0)
    assert s.genlik_katsayisi == pytest.approx(0.1)


def test_tek_yon_secenegi():
    s = ZayiflamaModeli().hesapla(ZayiflamaGirdisi(2.0, 3.0, gidis_donus=False))
    assert s.toplam_yol_m == pytest.approx(2.0)
    assert s.toplam_kayip_db == pytest.approx(6.0)


def test_geometrik_yayilim_referans_mesafede_ek_kayip_uretmez():
    s = ZayiflamaModeli().hesapla(ZayiflamaGirdisi(
        0.5, 0.0, geometrik_yayilim=True, referans_mesafe_m=1.0
    ))
    assert s.toplam_yol_m == pytest.approx(1.0)
    assert s.geometrik_kayip_db == pytest.approx(0.0)


def test_geometrik_yayilim_mesafe_artinca_kaybi_artirir():
    model = ZayiflamaModeli()
    a = model.hesapla(ZayiflamaGirdisi(1.0, 0.0, geometrik_yayilim=True))
    b = model.hesapla(ZayiflamaGirdisi(2.0, 0.0, geometrik_yayilim=True))
    assert b.geometrik_kayip_db > a.geometrik_kayip_db
    assert b.genlik_katsayisi < a.genlik_katsayisi


def test_geometrik_us_sifirsa_ek_kayip_yoktur():
    s = ZayiflamaModeli().hesapla(ZayiflamaGirdisi(
        2.0, 0.0, geometrik_yayilim=True, geometrik_us=0.0
    ))
    assert s.geometrik_kayip_db == pytest.approx(0.0)
    assert s.genlik_katsayisi == pytest.approx(1.0)


@pytest.mark.parametrize('alan,deger', [
    ('tek_yon_mesafe_m', -0.1),
    ('ortam_zayiflama_db_m', -0.1),
    ('referans_mesafe_m', 0.0),
    ('geometrik_us', -1.0),
])
def test_gecersiz_girdiler_reddedilir(alan, deger):
    veri = dict(tek_yon_mesafe_m=1.0, ortam_zayiflama_db_m=1.0)
    veri[alan] = deger
    with pytest.raises(ValueError):
        ZayiflamaModeli().hesapla(ZayiflamaGirdisi(**veri))


def test_dalga_motorunda_geometrik_yayilim_genligi_dusurur():
    ortam = OrtamModeli('su', yayilim_hizi_m_s=1500.0, zayiflama_db_m=0.0)
    ortak = dict(
        ortam=ortam, derinlik_m=2.0, frekans_hz=1000.0,
        ornekleme_hz=10000.0, sure_s=0.02, baslangic_genligi=1.0,
        yansima_katsayisi=1.0,
    )
    motor = DalgaYayilimMotoru()
    a = motor.uret(DalgaYayilimGirdisi(**ortak, geometrik_yayilim=False))
    b = motor.uret(DalgaYayilimGirdisi(**ortak, geometrik_yayilim=True))
    assert max(map(abs, b.genlik)) < max(map(abs, a.genlik))


def test_dalga_motoru_varsayilan_davranisi_korur():
    ortam = OrtamModeli('su', yayilim_hizi_m_s=1500.0, zayiflama_db_m=2.0)
    g = DalgaYayilimGirdisi(
        ortam=ortam, derinlik_m=1.0, frekans_hz=1000.0,
        ornekleme_hz=10000.0, sure_s=0.01,
    )
    sonuc = DalgaYayilimMotoru().uret(g)
    assert len(sonuc.genlik) == 100
