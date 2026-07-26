from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import cmath
import math
from typing import Sequence


class PencereTuru(StrEnum):
    DIKDORTGEN = "dikdortgen"
    HANN = "hann"
    HAMMING = "hamming"


@dataclass(frozen=True, slots=True)
class SpektrumTepesi:
    frekans_hz: float
    genlik: float
    bin_index: int


@dataclass(frozen=True, slots=True)
class FrekansCozumlemeSonucu:
    frekans_hz: tuple[float, ...]
    genlik: tuple[float, ...]
    guc: tuple[float, ...]
    dc_genligi: float
    nyquist_hz: float
    frekans_cozunurlugu_hz: float
    pencere: PencereTuru
    baskin_tepe: SpektrumTepesi | None
    yontem: str
    varsayimlar: tuple[str, ...]


def _dogrula_sinyal(sinyal: Sequence[float]) -> tuple[float, ...]:
    if not sinyal:
        raise ValueError("sinyal boş olamaz")
    sonuc = tuple(float(x) for x in sinyal)
    if any(not math.isfinite(x) for x in sonuc):
        raise ValueError("sinyal yalnız sonlu sayılardan oluşmalıdır")
    return sonuc


def pencere_katsayilari(tur: PencereTuru, n: int) -> tuple[float, ...]:
    if n <= 0:
        raise ValueError("örnek sayısı pozitif olmalıdır")
    if n == 1:
        return (1.0,)
    if tur == PencereTuru.DIKDORTGEN:
        return (1.0,) * n
    if tur == PencereTuru.HANN:
        return tuple(0.5 - 0.5 * math.cos(2.0 * math.pi * i / (n - 1)) for i in range(n))
    if tur == PencereTuru.HAMMING:
        return tuple(0.54 - 0.46 * math.cos(2.0 * math.pi * i / (n - 1)) for i in range(n))
    raise ValueError(f"desteklenmeyen pencere türü: {tur}")


class FrekansCozumleyici:
    """Tek taraflı DFT tabanlı referans spektrum çözümleyici.

    Bu sürüm dış bağımlılık kullanmaz ve küçük/orta referans dizileri için
    deterministik doğrulama amacı taşır. Yüksek performanslı FFT değildir.
    """

    YONTEM = "tek_tarafli_dft_referans"
    VARSAYIMLAR = (
        "ornekleme_araligi_sabit",
        "sinyal_gercek_degerli",
        "pencere_genlik_duzeltmesi_toplam_katsayi_ile_yapilir",
    )

    def coz(
        self,
        sinyal: Sequence[float],
        *,
        ornekleme_hz: float,
        pencere: PencereTuru = PencereTuru.HANN,
        dc_haric_tepe: bool = True,
    ) -> FrekansCozumlemeSonucu:
        x = _dogrula_sinyal(sinyal)
        if not math.isfinite(ornekleme_hz) or ornekleme_hz <= 0:
            raise ValueError("ornekleme_hz pozitif ve sonlu olmalıdır")

        n = len(x)
        w = pencere_katsayilari(pencere, n)
        pencere_toplami = sum(w)
        if pencere_toplami == 0:
            raise ValueError("pencere toplamı sıfır olamaz")

        xw = tuple(a * b for a, b in zip(x, w))
        son_bin = n // 2
        frekanslar: list[float] = []
        genlikler: list[float] = []
        gucler: list[float] = []

        for k in range(son_bin + 1):
            toplam = 0j
            for i, deger in enumerate(xw):
                toplam += deger * cmath.exp(-2j * math.pi * k * i / n)

            genlik = abs(toplam) / pencere_toplami
            if k != 0 and not (n % 2 == 0 and k == n // 2):
                genlik *= 2.0

            frekanslar.append(k * ornekleme_hz / n)
            genlikler.append(genlik)
            gucler.append(genlik * genlik)

        baslangic = 1 if dc_haric_tepe and len(genlikler) > 1 else 0
        baskin: SpektrumTepesi | None = None
        if genlikler[baslangic:]:
            index = max(range(baslangic, len(genlikler)), key=lambda i: genlikler[i])
            baskin = SpektrumTepesi(
                frekans_hz=frekanslar[index],
                genlik=genlikler[index],
                bin_index=index,
            )

        return FrekansCozumlemeSonucu(
            frekans_hz=tuple(frekanslar),
            genlik=tuple(genlikler),
            guc=tuple(gucler),
            dc_genligi=genlikler[0],
            nyquist_hz=ornekleme_hz / 2.0,
            frekans_cozunurlugu_hz=ornekleme_hz / n,
            pencere=pencere,
            baskin_tepe=baskin,
            yontem=self.YONTEM,
            varsayimlar=self.VARSAYIMLAR,
        )


def frekans_cozumle(
    sinyal: Sequence[float],
    *,
    ornekleme_hz: float,
    pencere: PencereTuru = PencereTuru.HANN,
) -> FrekansCozumlemeSonucu:
    return FrekansCozumleyici().coz(
        sinyal,
        ornekleme_hz=ornekleme_hz,
        pencere=pencere,
    )
