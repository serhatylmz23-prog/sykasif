from syk_simulasyon import (
    DalgaYayilimGirdisi,
    DalgaYayilimMotoru,
    HamSinyalBirlesimMotoru,
    SinyalBileseni,
    DSPPipeline,
)

from syk_simulasyon.dsp_olay_adaptoru import dsp_sonucunu_olaya_cevir
from syk_simulasyon.ortam_modeli import OrtamModeli
from syk_simulasyon.ortak_dil import Katman
from syk_simulasyon.olay_omurgasi import OlayTuru


def test_dsp_sonucu_kanit_olayina_donusur():

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
        )
    )

    ham = HamSinyalBirlesimMotoru().birlestir(
        [
            SinyalBileseni(
                ad="sentetik_yanki",
                genlik=dalga.genlik,
                ornekleme_hz=10000.0,
            )
        ],
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0008",
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

    olay = dsp_sonucunu_olaya_cevir(
        dsp,
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0008",
    )

    assert olay.tur == OlayTuru.KANIT
    assert olay.kaynak == Katman.ANALIZ
    assert olay.hedef == Katman.BILGE_KAAN