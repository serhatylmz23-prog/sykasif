import pytest
from syk_simulasyon.model import *

def kaynak(p=0.9):
    return KaynakReferansi(VeriKaynagi.LITERATUR, "K-1", guven_puani=p)

def test_derinlik_ilk_asama_siniri():
    with pytest.raises(ValueError):
        SimulasyonKaydi("metal", 2.3, [kaynak()], {}, {})

def test_guven_celiski_ve_bilinmezlikle_duser():
    k = SimulasyonKaydi("bosluk", 1.5, [kaynak()], {}, {},
        celiskiler=[Celiski("jeoloji", "uygun", "uygunsuz", "guven_duser")],
        bilinmezlikler=[BilinmezlikNedeni.OLCUM_YOK])
    assert k.guven_puani() == 0.68

def test_bilinmeyen_acik_ifade_uretir():
    k = SimulasyonKaydi("mineral", 1.0, [kaynak()], {}, {}, bilinmezlikler=[BilinmezlikNedeni.VERI_YETERSIZ])
    assert "yetersiz" in k.kanit_ozeti()["ifade"].lower()

def test_arastirma_onceligi_hesaplanir():
    o = ArastirmaOnerisi("Nem varyasyonu", "Belirsizliği azaltır", 0.9, 0.2, 0.1)
    assert 0.8 < o.oncelik_puani <= 1.0

def test_icerik_sha_kararli():
    k = SimulasyonKaydi("metal", 0.8, [kaynak()], {"nem": 0.2}, {"frekans": 7000})
    assert k.icerik_ozeti_sha256() == k.icerik_ozeti_sha256()
