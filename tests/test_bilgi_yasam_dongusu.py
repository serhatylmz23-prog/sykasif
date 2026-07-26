from datetime import datetime, timedelta, timezone
import pytest

from syk_simulasyon.bilgi_yasam_dongusu import (
    BilgiCatismasi,
    BilgiDurumu,
    BilgiKaydi,
    HataHafizasi,
    HataKaydi,
    HataTuru,
    YasamDongusuKarari,
    catismalari_bul,
    durum_gecisi_uygula,
)


def bilgi(**degisiklik):
    veri = dict(
        baslik="Bakır 1 metre referansı",
        icerik_ozeti="Sanal deney sonucu",
        kaynak_kimlikleri=("K-1",),
        gecerlilik_suresi_gun=30,
    )
    veri.update(degisiklik)
    kayit = BilgiKaydi(**veri)
    kayit.guven_ekle(0.60, "ilk değerlendirme")
    return kayit


def test_guven_gecmisi_ve_guncel_guven():
    kayit = bilgi()
    kayit.guven_ekle(0.75, "tekrarlanan simülasyon")
    assert kayit.guncel_guven == 0.75
    assert len(kayit.guven_gecmisi) == 2


def test_eskime_tespiti():
    kayit = bilgi()
    kayit.son_inceleme = datetime.now(timezone.utc) - timedelta(days=31)
    assert kayit.eskidi_mi()


def test_eskime_durumu_degistirir():
    kayit = bilgi()
    kayit.son_inceleme = datetime.now(timezone.utc) - timedelta(days=31)
    assert kayit.yeniden_dogrulama_durumu()
    assert kayit.durum == BilgiDurumu.YENIDEN_DOGRULAMA_GEREKLI


def test_yeni_kaynak_yeniden_dogrulama_tetikler():
    kayit = bilgi()
    assert kayit.yeniden_dogrulama_durumu(yeni_kaynak_var=True)


def test_guven_zinciri_kanitlarla_artabilir():
    kayit = bilgi(tekrar_sayisi=2, bagimsiz_dogrulandi=True, simulasyonla_uyumlu=True)
    assert kayit.guven_zinciri_puani() > kayit.guncel_guven


def test_saha_uyumsuzlugu_guveni_dusurur():
    kayit = bilgi(sahayla_uyumlu=False)
    assert kayit.guven_zinciri_puani() < kayit.guncel_guven


def test_bilge_kaan_onayi_olmadan_durum_degismez():
    kayit = bilgi()
    karar = YasamDongusuKarari(kayit.bilgi_id, BilgiDurumu.KULLANIMDA, "uygun", False)
    with pytest.raises(PermissionError):
        durum_gecisi_uygula(kayit, karar)


def test_kullanim_durumu_bilge_kaan_onayiyla_degisebilir():
    kayit = bilgi()
    karar = YasamDongusuKarari(kayit.bilgi_id, BilgiDurumu.KULLANIMDA, "uygun", True)
    durum_gecisi_uygula(kayit, karar)
    assert kayit.durum == BilgiDurumu.KULLANIMDA


def test_gecersiz_kilma_kurucu_kaan_onayi_ister():
    kayit = bilgi()
    karar = YasamDongusuKarari(kayit.bilgi_id, BilgiDurumu.GECERSIZ, "çelişkili", True, False)
    with pytest.raises(PermissionError):
        durum_gecisi_uygula(kayit, karar)


def test_gecersiz_kilma_cift_onayla_uygulanir():
    kayit = bilgi()
    karar = YasamDongusuKarari(kayit.bilgi_id, BilgiDurumu.GECERSIZ, "çelişkili", True, True)
    durum_gecisi_uygula(kayit, karar)
    assert kayit.durum == BilgiDurumu.GECERSIZ


def test_catisma_ayni_kayitla_olusturulamaz():
    with pytest.raises(ValueError):
        BilgiCatismasi("BK-1", "BK-1", "konu", "fark")


def test_catisma_motoru_farkli_sonuclari_bulur():
    birinci = bilgi(icerik_ozeti="yüksek tepki", sahayla_uyumlu=True)
    ikinci = bilgi(icerik_ozeti="düşük tepki", sahayla_uyumlu=False)
    ikinci.guven_gecmisi.clear()
    ikinci.guven_ekle(0.20, "uyumsuz sonuç")
    sonuclar = catismalari_bul([birinci, ikinci])
    assert len(sonuclar) == 1
    assert sonuclar[0].tekrar_deneyleri


def test_hata_hafizasi_ayni_hatayi_birlestirir():
    hafiza = HataHafizasi()
    hata = HataKaydi(HataTuru.PARAMETRE, "Kazanç fazla", {"ortam": "nemli"}, "Kazancı düşür")
    hafiza.kaydet(hata)
    ikinci = HataKaydi(HataTuru.PARAMETRE, "Kazanç fazla", {"ortam": "nemli"}, "Kazancı düşür")
    sonuc = hafiza.kaydet(ikinci)
    assert sonuc.tekrar_sayisi == 2
    assert len(hafiza.benzer_hatalar(HataTuru.PARAMETRE, 2)) == 1


def test_hata_hafizasi_deney_oncesi_uyari_verir():
    hafiza = HataHafizasi()
    hafiza.kaydet(HataKaydi(HataTuru.GORSEL, "Yansıma", {"isik": "yüksek"}, "Işığı azalt"))
    assert hafiza.deney_icin_uyarilar({"isik": "yüksek"}) == ("Işığı azalt",)


def test_parmak_izi_ayni_icerikte_sabittir():
    a = bilgi()
    b = bilgi()
    assert a.icerik_parmak_izi() == b.icerik_parmak_izi()
