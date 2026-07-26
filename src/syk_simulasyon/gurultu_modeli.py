from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math
import random
from typing import Sequence


class GurultuTuru(StrEnum):
    BEYAZ = "beyaz"
    SAPMA = "sapma"
    TITRESIM = "titresim"
    DARBE = "darbe"
    KAYIP = "kayip"


@dataclass(frozen=True, slots=True)
class GurultuProfili:
    beyaz_std: float = 0.0
    sapma_genligi: float = 0.0
    sapma_frekansi_hz: float = 0.0
    titresim_genligi: float = 0.0
    titresim_frekansi_hz: float = 0.0
    darbe_olasiligi: float = 0.0
    darbe_genligi: float = 0.0
    kayip_olasiligi: float = 0.0
    rastgele_tohum: int = 0

    def dogrula(self, ornekleme_hz: float) -> None:
        sayisal_degerler = (
            ornekleme_hz,
            self.beyaz_std,
            self.sapma_genligi,
            self.sapma_frekansi_hz,
            self.titresim_genligi,
            self.titresim_frekansi_hz,
            self.darbe_olasiligi,
            self.darbe_genligi,
            self.kayip_olasiligi,
        )
        if any(not math.isfinite(deger) for deger in sayisal_degerler):
            raise ValueError("profil degerleri sonlu sayilar olmalidir")
        if ornekleme_hz <= 0:
            raise ValueError("ornekleme_hz pozitif olmalıdır")
        if self.beyaz_std < 0:
            raise ValueError("beyaz_std negatif olamaz")
        if self.sapma_genligi < 0 or self.titresim_genligi < 0:
            raise ValueError("gürültü genlikleri negatif olamaz")
        if self.sapma_frekansi_hz < 0 or self.titresim_frekansi_hz < 0:
            raise ValueError("gürültü frekansları negatif olamaz")
        nyquist = ornekleme_hz / 2.0
        if self.sapma_frekansi_hz > nyquist or self.titresim_frekansi_hz > nyquist:
            raise ValueError("gürültü frekansı Nyquist sınırını aşamaz")
        if not 0.0 <= self.darbe_olasiligi <= 1.0:
            raise ValueError("darbe_olasiligi 0 ile 1 arasında olmalıdır")
        if not 0.0 <= self.kayip_olasiligi <= 1.0:
            raise ValueError("kayip_olasiligi 0 ile 1 arasında olmalıdır")
        if self.darbe_genligi < 0:
            raise ValueError("darbe_genligi negatif olamaz")


@dataclass(frozen=True, slots=True)
class GurultuSonucu:
    genlik: tuple[float, ...]
    beyaz_bilesen: tuple[float, ...]
    sapma_bilesen: tuple[float, ...]
    titresim_bilesen: tuple[float, ...]
    darbe_bilesen: tuple[float, ...]
    kayip_maskesi: tuple[bool, ...]
    kullanilan_turler: tuple[GurultuTuru, ...]
    varsayimlar: tuple[str, ...]


class GurultuModeli:
    """Tekrar üretilebilir sentetik gürültü üretir.

    Bu model gerçek cihaz gürültü spektrumunu temsil etmez. Gürültü profili
    doğrulanmış cihaz veya sanal laboratuvar kaynağından ayrıca sağlanmalıdır.
    """

    VARSAYIMLAR = (
        "beyaz_gurultu_gauss",
        "sapma_sinuz",
        "titresim_sinuz",
        "darbe_bernoulli",
        "kayip_bernoulli",
    )

    def uygula(
        self,
        temiz_sinyal: Sequence[float],
        *,
        ornekleme_hz: float,
        profil: GurultuProfili,
    ) -> GurultuSonucu:
        profil.dogrula(ornekleme_hz)
        temiz = tuple(float(x) for x in temiz_sinyal)
        if not temiz:
            raise ValueError("temiz_sinyal boş olamaz")
        if any(not math.isfinite(x) for x in temiz):
            raise ValueError("temiz_sinyal sonlu sayılardan oluşmalıdır")

        rng = random.Random(profil.rastgele_tohum)
        beyaz: list[float] = []
        sapma: list[float] = []
        titresim: list[float] = []
        darbe: list[float] = []
        kayip: list[bool] = []
        cikti: list[float] = []

        for i, taban in enumerate(temiz):
            t = i / ornekleme_hz
            b = rng.gauss(0.0, profil.beyaz_std) if profil.beyaz_std else 0.0
            s = (
                profil.sapma_genligi * math.sin(2.0 * math.pi * profil.sapma_frekansi_hz * t)
                if profil.sapma_genligi and profil.sapma_frekansi_hz
                else 0.0
            )
            tr = (
                profil.titresim_genligi * math.sin(2.0 * math.pi * profil.titresim_frekansi_hz * t)
                if profil.titresim_genligi and profil.titresim_frekansi_hz
                else 0.0
            )
            d = 0.0
            if profil.darbe_olasiligi and rng.random() < profil.darbe_olasiligi:
                d = profil.darbe_genligi * (1.0 if rng.random() >= 0.5 else -1.0)
            kayip_mi = bool(profil.kayip_olasiligi and rng.random() < profil.kayip_olasiligi)

            deger = 0.0 if kayip_mi else taban + b + s + tr + d
            beyaz.append(b)
            sapma.append(s)
            titresim.append(tr)
            darbe.append(d)
            kayip.append(kayip_mi)
            cikti.append(deger)

        turler: list[GurultuTuru] = []
        if profil.beyaz_std:
            turler.append(GurultuTuru.BEYAZ)
        if profil.sapma_genligi:
            turler.append(GurultuTuru.SAPMA)
        if profil.titresim_genligi:
            turler.append(GurultuTuru.TITRESIM)
        if profil.darbe_olasiligi:
            turler.append(GurultuTuru.DARBE)
        if profil.kayip_olasiligi:
            turler.append(GurultuTuru.KAYIP)

        return GurultuSonucu(
            genlik=tuple(cikti),
            beyaz_bilesen=tuple(beyaz),
            sapma_bilesen=tuple(sapma),
            titresim_bilesen=tuple(titresim),
            darbe_bilesen=tuple(darbe),
            kayip_maskesi=tuple(kayip),
            kullanilan_turler=tuple(turler),
            varsayimlar=self.VARSAYIMLAR,
        )
