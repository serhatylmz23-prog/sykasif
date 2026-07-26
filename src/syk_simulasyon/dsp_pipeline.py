from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .dsp_dc_kayma import DCKaymaGiderici, DCKaymaSonucu
from .dsp_bant_geciren import (
    BantGecirenAyar,
    BantGecirenSonucu,
    BantGecirenSuzgec,
)
from .dsp_frekans_cozumleme import (
    FrekansCozumlemeSonucu,
    FrekansCozumleyici,
    PencereTuru,
)


@dataclass(frozen=True, slots=True)
class DSPPipelineSonucu:
    dc_sonucu: DCKaymaSonucu
    filtre_sonucu: BantGecirenSonucu
    spektrum_sonucu: FrekansCozumlemeSonucu
    yontem: str
    varsayimlar: tuple[str, ...]


class DSPPipeline:
    """Temel DSP işlem zincirini sırayla uygular.

    Akış:
    sinyal
      -> DC kayma giderme
      -> bant geçiren FIR filtre
      -> frekans çözümleme

    İlk referans sürümüdür. Gerçek cihaz kalibrasyonu veya
    adaptif filtre davranışı içermez.
    """

    YONTEM = "dc_kayma_bant_filtre_frekans_analiz_zinciri"

    VARSAYIMLAR = (
        "islem_sirasi_sabit",
        "ornekleme_hizi_sabit",
        "filtre_ve_spektrum_modulleri_referans_cekirdektir",
    )

    def uygula(
        self,
        sinyal: Sequence[float],
        *,
        ornekleme_hz: float,
        alt_kesim_hz: float,
        ust_kesim_hz: float,
        filtre_sira: int = 101,
        pencere: PencereTuru = PencereTuru.HANN,
    ) -> DSPPipelineSonucu:

        if not math.isfinite(ornekleme_hz) or ornekleme_hz <= 0:
            raise ValueError(
                "ornekleme_hz pozitif ve sonlu olmalidir"
            )

        dc = DCKaymaGiderici().uygula(sinyal)

        ayar = BantGecirenAyar(
            alt_kesim_hz=alt_kesim_hz,
            ust_kesim_hz=ust_kesim_hz,
            ornekleme_hz=ornekleme_hz,
            sira=filtre_sira,
        )

        filtre = BantGecirenSuzgec().uygula(
            dc.cikti,
            ayar,
        )

        spektrum = FrekansCozumleyici().coz(
            filtre.cikti,
            ornekleme_hz=ornekleme_hz,
            pencere=pencere,
        )

        return DSPPipelineSonucu(
            dc_sonucu=dc,
            filtre_sonucu=filtre,
            spektrum_sonucu=spektrum,
            yontem=self.YONTEM,
            varsayimlar=self.VARSAYIMLAR,
        )