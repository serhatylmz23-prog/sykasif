import pytest
from syk_simulasyon.arastirma_veri_bankasi import ArastirmaVeriBankasi, GeriAlmaTalebi


def test_kodlanmis_kimlikler_ve_deney_numarasi():
    banka = ArastirmaVeriBankasi()
    ak = banka.arastirma_ac("R-01", "A-07")
    dn = banka.deney_ekle(ak, {"derinlik_m":1.25})
    assert ak.startswith("AK-") and dn.startswith("DN-")
    assert "derinlik" not in ak.lower() and "derinlik" not in dn.lower()


def test_karar_defteri_hash_zinciri():
    banka = ArastirmaVeriBankasi()
    ak = banka.arastirma_ac("R-01", "A-07")
    banka.karar_ekle(ak, "ONERI", "ilk", True, False)
    banka.karar_ekle(ak, "ONAY", "ikinci", True, True)
    assert banka.karar_zincirini_dogrula()


def test_geri_alma_cift_onay_ister():
    banka = ArastirmaVeriBankasi()
    ak = banka.arastirma_ac("R-01", "A-07")
    karar = banka.karar_ekle(ak, "GUNCELLE", "deneme", True, True)
    with pytest.raises(PermissionError):
        banka.geri_al(GeriAlmaTalebi("T-1", ak, karar, "geri", True, False))
    kimlik = banka.geri_al(GeriAlmaTalebi("T-2", ak, karar, "geri", True, True))
    assert kimlik.startswith("KD-")


def test_hedef_evrim_dosyasi_surumludur():
    banka = ArastirmaVeriBankasi()
    assert banka.hedef_surumu_ekle("H-1", "ILK", {"durum":"A"}) == 1
    assert banka.hedef_surumu_ekle("H-1", "ASINMA", {"durum":"B"}) == 2


def test_geri_alma_gecmisi_kalici_kaydedilir():
    banka = ArastirmaVeriBankasi()
    ak = banka.arastirma_ac("R-02", "A-08")
    karar = banka.karar_ekle(ak, "GUNCELLE", "deneme", True, True)
    banka.geri_al(GeriAlmaTalebi("T-KALICI", ak, karar, "geri", True, True))
    gecmis = banka.geri_alma_gecmisi(ak)
    assert len(gecmis) == 1 and gecmis[0]["hedef_karar_kimligi"] == karar


def test_olmayan_karar_geri_alinamaz():
    banka = ArastirmaVeriBankasi()
    ak = banka.arastirma_ac("R-02", "A-08")
    with pytest.raises(KeyError):
        banka.geri_al(GeriAlmaTalebi("T-X", ak, "KD-YOK", "geri", True, True))


def test_politika_kaydi_butunlugu():
    banka = ArastirmaVeriBankasi()
    sha = banka.politika_kaydet("KP-1", 1, "etkin", {"alan":"frekans_hz", "min":5000, "max":15000})
    assert len(sha) == 64 and banka.politika_butunlugunu_dogrula("KP-1")


def test_veri_bankasi_yedegi_acilabilir(tmp_path):
    banka = ArastirmaVeriBankasi()
    banka.arastirma_ac("R-03", "A-09")
    yedek = banka.yedekle(tmp_path / "yedek.sqlite3")
    diger = ArastirmaVeriBankasi(yedek)
    assert diger.db.execute("SELECT COUNT(*) FROM arastirma").fetchone()[0] == 1


def test_genel_butunluk_kontrolu():
    banka = ArastirmaVeriBankasi()
    ak = banka.arastirma_ac("R-04", "A-10")
    banka.karar_ekle(ak, "ONERI", "gerekçe", True, False)
    assert banka.butunluk_kontrolu()
