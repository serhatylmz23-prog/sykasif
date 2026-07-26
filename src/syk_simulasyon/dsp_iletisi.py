from __future__ import annotations

from .ortak_dil import Katman, IletiTuru, OrtakIleti
from .dsp_pipeline import DSPPipelineSonucu


def dsp_sonucunu_ilet(
    sonuc: DSPPipelineSonucu,
    *,
    arastirma_kimligi: str,
) -> OrtakIleti:

    tepe = sonuc.spektrum_sonucu.baskin_tepe

    if tepe is None:
        raise ValueError("DSP sonucu baskin tepe icermiyor")

    return OrtakIleti.olustur(
        arastirma_kimligi=arastirma_kimligi,
        tur=IletiTuru.KANIT,
        kaynak_katman=Katman.SIMULASYON,
        hedef_katman=Katman.ANALIZ,
        ozet_kodu="DSP-0007",
        guven=1.0,
        icerik_ozeti="DSP analiz sonucu olusturuldu",
        ozel_icerik={
            "baskin_frekans_hz": tepe.frekans_hz,
            "baskin_genlik": tepe.genlik,
            "yontem": sonuc.yontem,
            "varsayimlar": sonuc.varsayimlar,
        },
    )