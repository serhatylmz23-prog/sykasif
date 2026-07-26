from syk_simulasyon.runtime_durumu import RuntimeDurumu
from syk_simulasyon.olay_omurgasi import Olay, OlayTuru
from syk_simulasyon.ortak_dil import Katman


def test_runtime_durumu_olaydan_guncellenir():
    durum = RuntimeDurumu()

    olay = Olay.olustur(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0009",
        tur=OlayTuru.KANIT,
        kaynak=Katman.ANALIZ,
        hedef=Katman.BILGE_KAAN,
        ozet_kodu="DSP-0008",
        ortak_veri={
            "kaynak": "DSPPipeline",
        },
        ozel_veri={
            "test": True,
        },
    )

    durum.guncelle(olay)

    gorunum = durum.gorunum()

    assert gorunum["aktif_katman"] == "K90"
    assert gorunum["son_olay_kodu"] == "DSP-0008"
    assert gorunum["son_olay_turu"] == "KANIT"
    assert gorunum["durum"] == "OLAY_ALINDI"