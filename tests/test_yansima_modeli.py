import math
import pytest

from syk_simulasyon.yansima_katsayilari import KatsayiDurumu, YansimaKatsayiKaydi
from syk_simulasyon.yansima_modeli import YansimaGirdisi, YansimaModeli
from syk_simulasyon.yansima_turleri import YansimaTuru
from syk_simulasyon.yuzey_modeli import YuzeyModeli


def katsayi(**degisiklik):
    veri = dict(
        katsayi_kimligi="YK-001",
        genlik_katsayisi=0.8,
        kaynak="sentetik_test_referansi",
        guven_0_1=0.5,
        durum=KatsayiDurumu.REFERANS,
        frekans_alt_hz=1000,
        frekans_ust_hz=10000,
    )
    veri.update(degisiklik)
    return YansimaKatsayiKaydi(**veri)


def yuzey(**degisiklik):
    veri = dict(yuzey_kimligi="YZ-001", puruzluluk_0_1=0.0)
    veri.update(degisiklik)
    return YuzeyModeli(**veri)


def hesapla(**degisiklik):
    veri = dict(gelen_genlik=2.0, frekans_hz=5000, gelis_acisi_derece=0.0,
                yuzey=yuzey(), katsayi=katsayi())
    veri.update(degisiklik)
    return YansimaModeli().hesapla(YansimaGirdisi(**veri))


def test_duzgun_puruzsuz_yuzey():
    sonuc = hesapla(yuzey=yuzey(yansima_turu=YansimaTuru.DUZGUN))
    assert sonuc.yansiyan_genlik == pytest.approx(1.6)


def test_doksan_derecede_yansima_sifira_yaklasir():
    assert hesapla(gelis_acisi_derece=90).yansiyan_genlik == pytest.approx(0.0, abs=1e-12)


def test_otuz_derece_kosinus_olcegi():
    sonuc = hesapla(gelis_acisi_derece=30, yuzey=yuzey(yansima_turu=YansimaTuru.DUZGUN))
    assert sonuc.aci_katsayisi == pytest.approx(math.cos(math.radians(30)))


def test_yuzey_yonelimi_bagil_aciyi_degistirir():
    sonuc = hesapla(gelis_acisi_derece=30, yuzey=yuzey(yonelim_derece=30, yansima_turu=YansimaTuru.DUZGUN))
    assert sonuc.aci_katsayisi == pytest.approx(1.0)


def test_puruzluluk_duzgun_yansimayi_azaltir():
    temiz = hesapla(yuzey=yuzey(puruzluluk_0_1=0, yansima_turu=YansimaTuru.DUZGUN))
    puruzlu = hesapla(yuzey=yuzey(puruzluluk_0_1=1, yansima_turu=YansimaTuru.DUZGUN))
    assert puruzlu.yansiyan_genlik < temiz.yansiyan_genlik


def test_puruzluluk_daginik_bileseni_artirir():
    az = hesapla(yuzey=yuzey(puruzluluk_0_1=0, yansima_turu=YansimaTuru.DAGINIK))
    cok = hesapla(yuzey=yuzey(puruzluluk_0_1=1, yansima_turu=YansimaTuru.DAGINIK))
    assert cok.yansiyan_genlik > az.yansiyan_genlik


def test_karma_yuzey_sinirli_sonuc_uretir():
    sonuc = hesapla(yuzey=yuzey(puruzluluk_0_1=.5, yansima_turu=YansimaTuru.KARMA))
    assert 0 <= sonuc.etkin_katsayi <= 1

@pytest.mark.parametrize("aci", [-1, 91])
def test_gecersiz_gelis_acisi_reddedilir(aci):
    with pytest.raises(ValueError):
        hesapla(gelis_acisi_derece=aci)


def test_veri_yetersiz_katsayi_reddedilir():
    with pytest.raises(ValueError, match="veri yetersiz"):
        hesapla(katsayi=katsayi(genlik_katsayisi=None, durum=KatsayiDurumu.VERI_YETERSIZ))


def test_kaynaksiz_katsayi_reddedilir():
    with pytest.raises(ValueError, match="kaynağı"):
        hesapla(katsayi=katsayi(kaynak=None))


def test_frekans_araligi_disi_reddedilir():
    with pytest.raises(ValueError, match="aralığının üstündedir"):
        hesapla(frekans_hz=11000)


def test_ayni_girdi_ayni_sonuc():
    assert hesapla() == hesapla()


def test_gelen_genlik_sifirsa_cikis_sifirdir():
    assert hesapla(gelen_genlik=0).yansiyan_genlik == 0
