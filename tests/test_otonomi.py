from syk_simulasyon.otonomi import *

def bilge():
    return BilgeKaanKontrolluOtonom({
        "frekans_hz": ParametreSiniri("frekans_hz", 5000, 15000, "Hz"),
        "hiz": ParametreSiniri("hiz", 0.5, 6.0, "km/saat"),
    })

def test_onayli_sinirda_anlik_uyarlama():
    assert bilge().degerlendir("arge_tarama", {"frekans_hz": 9000, "hiz": 2.0}) == Karar.ONAY

def test_sinir_disinda_bilge_ek_veri_ister():
    assert bilge().degerlendir("arge_tarama", {"frekans_hz": 18000}) == Karar.EK_VERI

def test_yasak_amac_guvenli_durdurur():
    b = bilge()
    assert b.degerlendir("istihbarat", {}) == Karar.GUVENLI_DURDUR
    assert b.aktif is False

def test_kurucu_kalici_terfi_icin_guclu_kanit_ister():
    k = KurucuKaanKontrolluOtonom()
    assert k.kalici_terfi_karari(Karar.ONAY, 0.79, True) == Karar.EK_VERI
    assert k.kalici_terfi_karari(Karar.ONAY, 0.90, True) == Karar.ONAY
