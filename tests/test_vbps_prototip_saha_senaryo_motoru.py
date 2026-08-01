from syk_core.entegrasyon.vbps_prototip_saha_senaryo_motoru import (
    VBPSPrototipSahaSenaryoMotoru,
)


def test_saha_senaryo():
    sistem = VBPSPrototipSahaSenaryoMotoru()

    sonuc = sistem.calistir(
        "SAHA-TEST-001",
        "BALIK_BULUCU",
        "HAZIR",
        "HAZIR",
        "HAZIR",
        "HAZIR",
    )

    assert sonuc.sonuc == "SAHA_SENARYO_BASARILI"
    assert len(sonuc.sha256) == 64
    assert sistem.dogrula(sonuc) is True


def test_cihaz_turu_hazirlik_durumu_olarak_degerlendirilmez():
    sistem = VBPSPrototipSahaSenaryoMotoru()

    sonuc = sistem.calistir(
        "SAHA-TEST-002",
        "GARMIN_9SV_GT23",
        "HAZIR",
        "HAZIR",
        "HAZIR",
        "HAZIR",
    )

    assert sonuc.sonuc == "SAHA_SENARYO_BASARILI"
    assert sistem.dogrula(sonuc) is True


def test_eksik_islem_adimi_inceleme_gerektirir():
    sistem = VBPSPrototipSahaSenaryoMotoru()

    sonuc = sistem.calistir(
        "SAHA-TEST-003",
        "BALIK_BULUCU",
        "HAZIR",
        "BEKLIYOR",
        "HAZIR",
        "HAZIR",
    )

    assert sonuc.sonuc == "INCELEME_GEREKLI"
    assert sistem.dogrula(sonuc) is True
