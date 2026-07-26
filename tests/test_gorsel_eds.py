import pytest
from syk_simulasyon.gorsel_eds import GorselEDSAnalizcisi, GorselKaliteOlcumu, GorselSorun


def test_iyi_goruntu_yuksek_puan_alir():
    s = GorselEDSAnalizcisi().analiz_et(GorselKaliteOlcumu(0.9, 0.1, 0.8, 0.1, True, 0.9))
    assert s.kalite_puani > 0.8
    assert not s.sorunlar


def test_kalite_sorunlari_ayri_ayri_isaretlenir():
    s = GorselEDSAnalizcisi().analiz_et(GorselKaliteOlcumu(0.2, 0.8, 0.2, 0.9, False, 0.2))
    assert GorselSorun.NETLIK_DUSUK in s.sorunlar
    assert GorselSorun.TITRESIM_YUKSEK in s.sorunlar
    assert GorselSorun.ISIK_YETERSIZ in s.sorunlar
    assert GorselSorun.YANSIMA_YUKSEK in s.sorunlar
    assert GorselSorun.GORUNTU_KAYBI in s.sorunlar
    assert GorselSorun.ODAK_BOZUK in s.sorunlar


def test_olcum_araligi_dogrulanir():
    with pytest.raises(ValueError):
        GorselKaliteOlcumu(1.1, 0.1, 0.8, 0.1, True, 0.9)
