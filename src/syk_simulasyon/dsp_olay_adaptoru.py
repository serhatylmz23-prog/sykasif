from __future__ import annotations

from .dsp_pipeline import DSPPipelineSonucu
from .olay_omurgasi import Olay, OlayTuru
from .ortak_dil import Katman


def dsp_sonucunu_olaya_cevir(
    sonuc: DSPPipelineSonucu,
    *,
    arastirma_kimligi: str,
    deney_numarasi: str | None = None,
) -> Olay:

    tepe = sonuc.spektrum_sonucu.baskin_tepe

    if tepe is None:
        raise ValueError("DSP sonucu baskin tepe icermiyor")

    return Olay.olustur(
        arastirma_kimligi=arastirma_kimligi,
        deney_numarasi=deney_numarasi,
        tur=OlayTuru.KANIT,
        kaynak=Katman.ANALIZ,
        hedef=Katman.BILGE_KAAN,
        ozet_kodu="DSP-0008",
        ortak_veri={
            "baskin_frekans_hz": tepe.frekans_hz,
            "kaynak": "DSPPipeline",
        },
        ozel_veri={
            "baskin_genlik": tepe.genlik,
            "yontem": sonuc.yontem,
            "varsayimlar": sonuc.varsayimlar,
        },
    )