import math
import pytest

from syk_simulasyon.dsp_pipeline import DSPPipeline


def sinyal_uret(frekans_hz, ornekleme_hz, n, genlik=1.0, dc=0.0):
    return tuple(
        dc + genlik * math.sin(2.0 * math.pi * frekans_hz * i / ornekleme_hz)
        for i in range(n)
    )


def test_dsp_pipeline_dc_kaymayi_giderir():
    sonuc = DSPPipeline().uygula(
        sinyal_uret(
            20.0,
            200.0,
            200,
            dc=5.0,
        ),
        ornekleme_hz=200.0,
        alt_kesim_hz=10.0,
        ust_kesim_hz=40.0,
    )

    assert sonuc.dc_sonucu.hesaplanan_kayma == pytest.approx(5.0, abs=0.1)


def test_dsp_pipeline_baskin_frekansi_bulur():
    sonuc = DSPPipeline().uygula(
        sinyal_uret(
            25.0,
            200.0,
            400,
        ),
        ornekleme_hz=200.0,
        alt_kesim_hz=10.0,
        ust_kesim_hz=40.0,
    )

    assert sonuc.spektrum_sonucu.baskin_tepe is not None
    assert sonuc.spektrum_sonucu.baskin_tepe.frekans_hz == pytest.approx(
        25.0,
        abs=1.0,
    )


def test_dsp_pipeline_yontem_kaydi_tutar():
    sonuc = DSPPipeline().uygula(
        (1.0, 2.0, 3.0, 4.0),
        ornekleme_hz=100.0,
        alt_kesim_hz=10.0,
        ust_kesim_hz=30.0,
        filtre_sira=21,
    )

    assert sonuc.yontem == "dc_kayma_bant_filtre_frekans_analiz_zinciri"