import pytest
from syk_simulasyon.oncelik_motoru import *


def oneri(kimlik="D-1", bilgi=0.9, risk=0.1, maliyet=0.2, durum=OneriDurumu.ADAY):
    return DeneyOnerisi(kimlik, "H-1", "0,5 metre nem varyasyonu", bilgi, 0.8, 0.6, maliyet, risk, 0.9, durum)


def test_puanlar_aralik_disinda_olamaz():
    with pytest.raises(ValueError):
        DeneyOnerisi("D", "H", "S", 1.2, 0, 0, 0, 0, 0)


def test_bilgi_kazanci_yuksek_oneri_onceliklidir():
    assert oneri(bilgi=0.9).oncelik_puani > oneri(kimlik="D-2", bilgi=0.2).oncelik_puani


def test_maliyet_ve_risk_puani_dusurur():
    assert oneri(risk=0.1, maliyet=0.1).oncelik_puani > oneri(kimlik="D-2", risk=0.9, maliyet=0.9).oncelik_puani


def test_ayni_senaryo_tekrar_edilmez():
    m = ArastirmaOncelikMotoru(); a = oneri(); m.kaydet(a)
    assert m.tekrar_mi(a)
    assert m.sirala([a]) == []


def test_reddedilen_oneri_siralanmaz():
    m = ArastirmaOncelikMotoru()
    assert m.sirala([oneri(durum=OneriDurumu.REDDEDILDI)]) == []


def test_siralama_puana_goredir():
    m = ArastirmaOncelikMotoru()
    dusuk = oneri("D-2", bilgi=0.2)
    yuksek = oneri("D-1", bilgi=0.9)
    assert [o.oneri_id for o in m.sirala([dusuk, yuksek])] == ["D-1", "D-2"]


def test_en_fazla_siniri_uygulanir():
    m = ArastirmaOncelikMotoru()
    assert len(m.sirala([oneri("D-1"), oneri("D-2")], en_fazla=1)) == 1


def test_bilge_kaan_incelemesine_esik_ustu_gider():
    m = ArastirmaOncelikMotoru()
    paket = m.bilge_kaan_incelemesine_hazirla([oneri()])
    assert paket[0]["durum"] == OneriDurumu.BILGE_KAAN_INCELEMESI


def test_parmak_izi_kimlikten_bagimsizdir():
    assert oneri("D-1").parmak_izi == oneri("D-2").parmak_izi
