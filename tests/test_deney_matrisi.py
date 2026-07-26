import pytest

from syk_simulasyon.deney_matrisi import (
    DerinlikPlani,
    FrekansOnerisi,
    HedefAnaSinifi,
    HedefTanim,
    KanitTuru,
    OrtamTanim,
    SimulasyonDeneyMatrisi,
)


def hedef():
    return HedefTanim(
        ana_sinif=HedefAnaSinifi.MALZEME,
        alt_sinif="bakir_ornek",
        malzeme_ozellikleri={"iletkenlik_s_m": 5.96e7},
        geometri="silindir",
        boyut_m=(0.10, 0.10, 0.02),
        yonelim_derece=0,
    )


def ortam():
    return OrtamTanim("kumlu_toprak", nem_orani=0.20, sicaklik_c=20, gurultu_puani=0.10)


def frekans(onay=True):
    return FrekansOnerisi(
        sensor_ailesi="ornek_sensor",
        alt_frekans_hz=5000,
        ust_frekans_hz=7000,
        adim_hz=1000,
        yayilim_hizi_m_s=1500,
        gerekce="Yalnız yazılım davranışını doğrulayan örnek aralık",
        kaynak_turu=KanitTuru.UZMAN_ONERISI,
        kaynak_kimligi="KNT-001",
        bilge_kaan_onay_kimligi="BK-ONAY-001" if onay else None,
    )


def test_temel_derinlik_plani_2_metrede_biter():
    plan = DerinlikPlani()
    assert max(plan.temel_noktalar_m) == 2.0
    assert len(plan.temel_noktalar_m) == 16


def test_temel_sinir_uzeri_reddedilir():
    with pytest.raises(ValueError):
        DerinlikPlani().dogrula(2.01)


def test_deneysel_sinir_225_metreye_kadar_acilabilir():
    DerinlikPlani().dogrula(2.20, deneysel=True)
    with pytest.raises(ValueError):
        DerinlikPlani().dogrula(2.26, deneysel=True)


def test_bilge_kaan_onayi_olmadan_frekans_matrisi_uretilmez():
    with pytest.raises(PermissionError):
        frekans(onay=False).frekanslar()


def test_dalga_boyu_yayilim_hizi_bol_frekans():
    assert frekans().dalga_boyu_m(5000) == pytest.approx(0.3)


def test_matriste_tum_bilesimler_uretilir():
    matris = SimulasyonDeneyMatrisi()
    sonuc = matris.uret([hedef()], [ortam()], frekans(), derinlikler_m=[0.5, 1.0])
    assert len(sonuc) == 6  # 1 hedef x 1 ortam x 2 derinlik x 3 frekans
    assert {s.derinlik_m for s in sonuc} == {0.5, 1.0}


def test_alt_sinif_zorunludur():
    with pytest.raises(ValueError):
        HedefTanim(HedefAnaSinifi.MINERAL, "")


def test_ortam_nemi_dogrulanir():
    with pytest.raises(ValueError):
        OrtamTanim("toprak", nem_orani=1.2, sicaklik_c=20)
