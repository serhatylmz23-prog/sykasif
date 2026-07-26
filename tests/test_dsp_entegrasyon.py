from syk_simulasyon import (
    DalgaYayilimGirdisi,
    DalgaYayilimMotoru,
    HamSinyalBirlesimMotoru,
    SinyalBileseni,
    DSPPipeline,
)
from syk_simulasyon.ortam_modeli import OrtamModeli


def test_dalga_ham_sinyal_dsp_zinciri():

    ortam = OrtamModeli(
        "su",
        yayilim_hizi_m_s=1500.0,
        zayiflama_db_m=0.0,
    )

    dalga = DalgaYayilimMotoru().uret(
        DalgaYayilimGirdisi(
            ortam=ortam,
            derinlik_m=1.0,
            frekans_hz=1000.0,
            ornekleme_hz=10000.0,
            sure_s=0.05,
            rastgele_tohum=42,
        )
    )

    bilesen = SinyalBileseni(
        ad="sentetik_yanki",
        genlik=dalga.genlik,
        ornekleme_hz=10000.0,
    )

    ham = HamSinyalBirlesimMotoru().birlestir(
        [bilesen],
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0006",
        ftsu_surumu="1.0",
        rastgele_tohum=42,
        parametre_ozeti={
            "frekans_hz": 1000.0,
        },
    )

    dsp = DSPPipeline().uygula(
        ham.genlik,
        ornekleme_hz=ham.ornekleme_hz,
        alt_kesim_hz=500.0,
        ust_kesim_hz=1500.0,
        filtre_sira=21,
    )

    assert dsp.spektrum_sonucu.baskin_tepe is not None
    assert dsp.spektrum_sonucu.baskin_tepe.frekans_hz == 1000.0