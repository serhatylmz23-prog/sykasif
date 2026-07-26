from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import fmean
from typing import Sequence


def _sonlu_dizi(dizi: Sequence[float], ad: str) -> tuple[float, ...]:
    if not dizi:
        raise ValueError(f"{ad} boş olamaz")
    sonuc = tuple(float(x) for x in dizi)
    if any(not math.isfinite(x) for x in sonuc):
        raise ValueError(f"{ad} yalnız sonlu sayılardan oluşmalıdır")
    return sonuc


@dataclass(frozen=True, slots=True)
class DCKaymaSonucu:
    girdi: tuple[float, ...]
    cikti: tuple[float, ...]
    hesaplanan_kayma: float
    cikti_ortalamasi: float
    ornek_sayisi: int
    yontem: str
    varsayimlar: tuple[str, ...]


class DCKaymaGiderici:
    """Sinyalin aritmetik ortalamasını çıkararak sabit kaymayı giderir.

    Bu ilk DSP referans çekirdeğidir. Zamanla değişen taban sürüklenmesini,
    yüksek dereceli eğilimleri veya cihaz özgü kalibrasyon davranışını modellemez.
    """

    YONTEM = "aritmetik_ortalama_cikarma"
    VARSAYIMLAR = (
        "kayma_sabit_kabul_edildi",
        "ornekler_esit_agirlikli_kabul_edildi",
    )

    def uygula(
        self,
        sinyal: Sequence[float],
        *,
        referans_baslangic: int | None = None,
        referans_bitis: int | None = None,
    ) -> DCKaymaSonucu:
        girdi = _sonlu_dizi(sinyal, "sinyal")

        baslangic = 0 if referans_baslangic is None else referans_baslangic
        bitis = len(girdi) if referans_bitis is None else referans_bitis

        if not isinstance(baslangic, int) or not isinstance(bitis, int):
            raise TypeError("referans sınırları tam sayı olmalıdır")
        if baslangic < 0 or bitis > len(girdi) or baslangic >= bitis:
            raise ValueError("geçersiz referans aralığı")

        referans = girdi[baslangic:bitis]
        kayma = fmean(referans)
        cikti = tuple(x - kayma for x in girdi)
        cikti_ortalamasi = fmean(cikti)

        return DCKaymaSonucu(
            girdi=girdi,
            cikti=cikti,
            hesaplanan_kayma=kayma,
            cikti_ortalamasi=cikti_ortalamasi,
            ornek_sayisi=len(girdi),
            yontem=self.YONTEM,
            varsayimlar=self.VARSAYIMLAR,
        )


def dc_kaymayi_gider(
    sinyal: Sequence[float],
    *,
    referans_baslangic: int | None = None,
    referans_bitis: int | None = None,
) -> tuple[float, ...]:
    """Kolay kullanım için yalnız düzeltilmiş sinyali döndürür."""
    return DCKaymaGiderici().uygula(
        sinyal,
        referans_baslangic=referans_baslangic,
        referans_bitis=referans_bitis,
    ).cikti
