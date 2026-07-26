import pytest
from syk_simulasyon.ortak_dil import Katman
from syk_simulasyon.olay_omurgasi import (
    BilgeKaanDenetimliOlayOmurgasi, GorevDurumu, KatmanKapisi,
    Olay, OlayTuru, yeni_gorev,
)


def omurga():
    return BilgeKaanDenetimliOlayOmurgasi(kapilar={
        Katman.SENSOR: KatmanKapisi(Katman.SENSOR, frozenset(), frozenset({OlayTuru.OLCUM})),
        Katman.ANALIZ: KatmanKapisi(Katman.ANALIZ, frozenset({OlayTuru.OLCUM}), frozenset({OlayTuru.ONERI})),
        Katman.BILGE_KAAN: KatmanKapisi(Katman.BILGE_KAAN, frozenset(set(OlayTuru)), frozenset(set(OlayTuru))),
        Katman.KURUCU_KAAN: KatmanKapisi(Katman.KURUCU_KAAN, frozenset({OlayTuru.ONERI}), frozenset()),
    })


def test_bilge_kaan_onayi_olmadan_yayin_yok():
    o = Olay.olustur(arastirma_kimligi="AK-X", deney_numarasi="DN-X", tur=OlayTuru.OLCUM,
        kaynak=Katman.SENSOR, hedef=Katman.ANALIZ, ozet_kodu="S01", ortak_veri={"deger": 1}, ozel_veri={"ham": [1,2]})
    with pytest.raises(PermissionError):
        omurga().yayinla(o, bilge_kaan_onayi=False)


def test_hedef_katman_ortak_gorunumu_okur():
    m = omurga(); o = Olay.olustur(arastirma_kimligi="AK-X", deney_numarasi="DN-X", tur=OlayTuru.OLCUM,
        kaynak=Katman.SENSOR, hedef=Katman.ANALIZ, ozet_kodu="S01", ortak_veri={"deger": 1}, ozel_veri={"ham": [1,2]})
    m.yayinla(o, bilge_kaan_onayi=True)
    assert m.oku(o.olay_kimligi, Katman.ANALIZ)["ozet_kodu"] == "S01"


def test_baska_katman_olayi_goremez():
    m = omurga(); o = Olay.olustur(arastirma_kimligi="AK-X", deney_numarasi=None, tur=OlayTuru.OLCUM,
        kaynak=Katman.SENSOR, hedef=Katman.ANALIZ, ozet_kodu="S01", ortak_veri={}, ozel_veri={"ham": 7})
    m.yayinla(o, bilge_kaan_onayi=True)
    with pytest.raises(PermissionError):
        m.oku(o.olay_kimligi, Katman.KURUCU_KAAN)


def test_ozel_analizi_yalniz_bilge_kaan_acar():
    m = omurga(); o = Olay.olustur(arastirma_kimligi="AK-X", deney_numarasi=None, tur=OlayTuru.OLCUM,
        kaynak=Katman.SENSOR, hedef=Katman.ANALIZ, ozet_kodu="S01", ortak_veri={}, ozel_veri={"ham": 7})
    m.yayinla(o, bilge_kaan_onayi=True)
    with pytest.raises(PermissionError):
        m.ozel_veriyi_ac(o.olay_kimligi, Katman.ANALIZ)
    assert m.ozel_veriyi_ac(o.olay_kimligi, Katman.BILGE_KAAN)["ham"] == 7


def test_kaynak_yetkisiz_olay_yayimlayamaz():
    m = omurga(); o = Olay.olustur(arastirma_kimligi="AK-X", deney_numarasi=None, tur=OlayTuru.ONERI,
        kaynak=Katman.SENSOR, hedef=Katman.KURUCU_KAAN, ozet_kodu="O01", ortak_veri={}, ozel_veri={})
    with pytest.raises(PermissionError):
        m.yayinla(o, bilge_kaan_onayi=True)


def test_gorev_bilge_kaan_onayi_olmadan_baslamaz():
    g = yeni_gorev(arastirma_kimligi="AK-X", deney_numarasi="DN-X", amac_kodu="A01", hedef_katman=Katman.SENSOR)
    with pytest.raises(PermissionError):
        g.baslat()


def test_gorev_onayla_baslar():
    g = yeni_gorev(arastirma_kimligi="AK-X", deney_numarasi="DN-X", amac_kodu="A01", hedef_katman=Katman.SENSOR)
    g.bilge_kaan_incele(True, "kanıt yeterli")
    g.baslat()
    assert g.durum == GorevDurumu.CALISIYOR


def test_geri_alma_cift_onay_ister():
    g = yeni_gorev(arastirma_kimligi="AK-X", deney_numarasi="DN-X", amac_kodu="A01", hedef_katman=Katman.SENSOR, geri_alma_plani="önceki profile dön")
    g.bilge_kaan_incele(True, "uygun"); g.baslat()
    with pytest.raises(PermissionError):
        g.geri_al(bilge_kaan_onayi=True, kurucu_kaan_onayi=False)
    g.geri_al(bilge_kaan_onayi=True, kurucu_kaan_onayi=True)
    assert g.durum == GorevDurumu.DURDURULDU
