import pytest
from syk_simulasyon.hedef_sicili import *


def kaynak(nitelik=KaynakNiteligi.BIRINCIL_BILIMSEL):
    return BilimselKaynak(
        "KAY-001", nitelik, "Örnek bilimsel kaynak", 2025,
        doi_veya_belge_no="10.0000/ornek", dogrudan_desteklenen_alanlar=("iletkenlik",)
    )


def bakir():
    return HedefAltSinifi(
        "HEDEF-MALZEME-BAKIR-001", HedefAilesi.MALZEME, "Bakır örneği",
        ozellikler=[FizikselOzellik("iletkenlik", 5.96e7, "S/m", "KAY-001")],
        izinli_geometriler=("levha", "silindir", "kure")
    )


def test_guclu_kaynak_belge_bilgisi_ister():
    with pytest.raises(ValueError):
        BilimselKaynak("K", KaynakNiteligi.BIRINCIL_BILIMSEL, "Başlık")


def test_malzeme_fiziksel_ozellik_ister():
    with pytest.raises(ValueError):
        HedefAltSinifi("H", HedefAilesi.MALZEME, "Bakır")


def test_hedef_eksik_kaynakla_eklenemez():
    with pytest.raises(ValueError):
        HedefSicili().hedef_ekle(bakir())


def test_hedef_kaynakla_eklenir():
    s = HedefSicili()
    s.kaynak_ekle(kaynak())
    s.hedef_ekle(bakir())
    assert s.hedefler["HEDEF-MALZEME-BAKIR-001"].ad == "Bakır örneği"


def test_ayni_kaynak_iki_kez_eklenemez():
    s = HedefSicili(); s.kaynak_ekle(kaynak())
    with pytest.raises(ValueError):
        s.kaynak_ekle(kaynak())


def test_ust_hedef_once_kaydedilmelidir():
    s = HedefSicili(); s.kaynak_ekle(kaynak())
    alt = bakir(); alt.ust_hedef_id = "YOK"
    with pytest.raises(ValueError):
        s.hedef_ekle(alt)


def test_aileye_gore_suzer():
    s = HedefSicili(); s.kaynak_ekle(kaynak()); s.hedef_ekle(bakir())
    assert len(s.aileye_gore(HedefAilesi.MALZEME)) == 1
    assert len(s.aileye_gore(HedefAilesi.MINERAL)) == 0


def test_hedef_guveni_kaynaktan_hesaplanir():
    s = HedefSicili(); s.kaynak_ekle(kaynak()); s.hedef_ekle(bakir())
    assert s.hedef_guven_puani("HEDEF-MALZEME-BAKIR-001") == pytest.approx(0.95)


def test_varsayim_ve_bilinmeyen_guveni_dusurur():
    s = HedefSicili(); s.kaynak_ekle(kaynak())
    h = HedefAltSinifi(
        "H2", HedefAilesi.MINERAL, "Örnek mineral",
        ozellikler=[FizikselOzellik("yoğunluk", 3.0, "g/cm3", "KAY-001", varsayim_mi=True)],
        bilinmeyen_alanlar=("dielektrik", "manyetik_gecirgenlik")
    )
    s.hedef_ekle(h)
    assert s.hedef_guven_puani("H2") < 0.70


def test_icerik_ozeti_kararlidir():
    h = bakir()
    assert h.icerik_sha256() == h.icerik_sha256()
