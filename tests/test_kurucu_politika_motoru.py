import pytest
from syk_simulasyon.kurucu_politika_motoru import (
    KurucuKaanPolitikaMotoru, KurucuPolitikasi, PolitikaDurumu,
    PolitikaSiniri, PolitikaTuru,
)


def politika():
    return KurucuPolitikasi(
        "Tarama frekansı sınırı",
        PolitikaTuru.ANLIK_UYARLAMA_SINIRI,
        "Anlık taramada yalnız onaylı aralık kullanılmalı",
        (PolitikaSiniri("frekans_hz", 5000, 15000),),
    )


def test_cift_onay_olmadan_etkinlesmez():
    m = KurucuKaanPolitikaMotoru(); p = m.kaydet(politika())
    m.bilge_kaan_incelemesine_gonder(p.politika_id)
    with pytest.raises(PermissionError):
        m.kurucu_kaan_onayla(p.politika_id)
    m.bilge_kaan_onayla(p.politika_id)
    m.kurucu_kaan_onayla(p.politika_id)
    assert p.durum == PolitikaDurumu.ETKIN


def test_etkin_politika_sinir_uygular():
    m = KurucuKaanPolitikaMotoru(); p = m.kaydet(politika())
    m.bilge_kaan_incelemesine_gonder(p.politika_id)
    m.bilge_kaan_onayla(p.politika_id); m.kurucu_kaan_onayla(p.politika_id)
    assert m.deger_izinli_mi(p.politika_id, "frekans_hz", 7000)
    assert not m.deger_izinli_mi(p.politika_id, "frekans_hz", 18000)


def test_kalici_geri_alma_cift_onay_ister():
    m = KurucuKaanPolitikaMotoru(); p = m.kaydet(politika())
    m.bilge_kaan_incelemesine_gonder(p.politika_id)
    m.bilge_kaan_onayla(p.politika_id); m.kurucu_kaan_onayla(p.politika_id)
    with pytest.raises(PermissionError):
        m.geri_al(p.politika_id, True, False)
    m.geri_al(p.politika_id, True, True)
    assert p.durum == PolitikaDurumu.GERI_ALINDI


def test_yeni_surum_onceki_politikaya_baglanir():
    m = KurucuKaanPolitikaMotoru(); p = m.kaydet(politika())
    yeni = m.yeni_surum(p.politika_id, "Yeni doğrulanmış sınır", (PolitikaSiniri("frekans_hz", 6000, 14000),))
    assert yeni.surum == 2 and yeni.onceki_politika_id == p.politika_id
