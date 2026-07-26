import math
import pytest

from syk_simulasyon.gurultu_modeli import (
    GurultuModeli,
    GurultuProfili,
    GurultuTuru,
)
from syk_simulasyon.dalga_yayilimi import DalgaYayilimGirdisi, DalgaYayilimMotoru
from syk_simulasyon.ortam_modeli import OrtamModeli


def test_sifir_profil_sinyali_degistirmez():
    temiz = (0.1, -0.2, 0.3)
    sonuc = GurultuModeli().uygula(temiz, ornekleme_hz=100.0, profil=GurultuProfili())
    assert sonuc.genlik == temiz
    assert sonuc.kullanilan_turler == ()


def test_beyaz_gurultu_tohumla_tekrar_uretilir():
    profil = GurultuProfili(beyaz_std=0.1, rastgele_tohum=42)
    a = GurultuModeli().uygula((0.0,) * 20, ornekleme_hz=100.0, profil=profil)
    b = GurultuModeli().uygula((0.0,) * 20, ornekleme_hz=100.0, profil=profil)
    assert a.genlik == b.genlik
    assert GurultuTuru.BEYAZ in a.kullanilan_turler


def test_farkli_tohum_farkli_sonuc_verir():
    a = GurultuModeli().uygula((0.0,) * 20, ornekleme_hz=100.0,
                              profil=GurultuProfili(beyaz_std=0.1, rastgele_tohum=1))
    b = GurultuModeli().uygula((0.0,) * 20, ornekleme_hz=100.0,
                              profil=GurultuProfili(beyaz_std=0.1, rastgele_tohum=2))
    assert a.genlik != b.genlik


def test_sapma_bileseni_sinuzdur():
    sonuc = GurultuModeli().uygula(
        (0.0,) * 5,
        ornekleme_hz=4.0,
        profil=GurultuProfili(sapma_genligi=1.0, sapma_frekansi_hz=1.0),
    )
    assert sonuc.sapma_bilesen == pytest.approx((0.0, 1.0, 0.0, -1.0, 0.0), abs=1e-12)


def test_titresim_bileseni_eklenir():
    sonuc = GurultuModeli().uygula(
        (1.0,) * 4,
        ornekleme_hz=4.0,
        profil=GurultuProfili(titresim_genligi=0.5, titresim_frekansi_hz=1.0),
    )
    assert sonuc.genlik == pytest.approx((1.0, 1.5, 1.0, 0.5), abs=1e-12)


def test_darbe_olasiligi_bir_ise_tum_orneklerde_darbe_olur():
    sonuc = GurultuModeli().uygula(
        (0.0,) * 10,
        ornekleme_hz=10.0,
        profil=GurultuProfili(darbe_olasiligi=1.0, darbe_genligi=2.0, rastgele_tohum=7),
    )
    assert all(abs(x) == 2.0 for x in sonuc.darbe_bilesen)


def test_kayip_olasiligi_bir_ise_tum_ornekler_sifirlanir():
    sonuc = GurultuModeli().uygula(
        (5.0,) * 10,
        ornekleme_hz=10.0,
        profil=GurultuProfili(kayip_olasiligi=1.0, rastgele_tohum=3),
    )
    assert sonuc.genlik == (0.0,) * 10
    assert all(sonuc.kayip_maskesi)


@pytest.mark.parametrize("alan,deger", [
    ("beyaz_std", -0.1),
    ("darbe_olasiligi", 1.1),
    ("kayip_olasiligi", -0.1),
    ("darbe_genligi", -1.0),
])
def test_gecersiz_profil_reddedilir(alan, deger):
    kwargs = {alan: deger}
    with pytest.raises(ValueError):
        GurultuModeli().uygula((0.0,), ornekleme_hz=10.0, profil=GurultuProfili(**kwargs))


def test_nyquist_siniri_asimi_reddedilir():
    with pytest.raises(ValueError):
        GurultuModeli().uygula(
            (0.0,) * 10,
            ornekleme_hz=10.0,
            profil=GurultuProfili(titresim_genligi=1.0, titresim_frekansi_hz=6.0),
        )


def test_bos_sinyal_reddedilir():
    with pytest.raises(ValueError):
        GurultuModeli().uygula((), ornekleme_hz=10.0, profil=GurultuProfili())


def test_sonlu_olmayan_sinyal_reddedilir():
    with pytest.raises(ValueError):
        GurultuModeli().uygula((math.nan,), ornekleme_hz=10.0, profil=GurultuProfili())


def test_dalga_motoruna_moduler_gurultu_entegredir():
    ortam = OrtamModeli(
        ortam_kimligi="ORT-1",
        yayilim_hizi_m_s=1500.0,
        zayiflama_db_m=0.0,
    )
    ortak = dict(
        ortam=ortam,
        derinlik_m=0.0,
        frekans_hz=10.0,
        ornekleme_hz=100.0,
        sure_s=0.1,
        baslangic_genligi=1.0,
        rastgele_tohum=5,
    )
    temiz = DalgaYayilimMotoru().uret(DalgaYayilimGirdisi(**ortak))
    gurultulu = DalgaYayilimMotoru().uret(DalgaYayilimGirdisi(
        **ortak,
        gurultu_profili=GurultuProfili(beyaz_std=0.1, rastgele_tohum=5),
    ))
    assert temiz.genlik != gurultulu.genlik
    assert len(temiz.genlik) == len(gurultulu.genlik)
