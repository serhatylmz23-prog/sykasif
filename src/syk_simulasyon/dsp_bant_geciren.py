from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


def _sonlu_sinyal(sinyal: Sequence[float]) -> tuple[float, ...]:
    if not sinyal:
        raise ValueError("sinyal boş olamaz")
    sonuc = tuple(float(x) for x in sinyal)
    if any(not math.isfinite(x) for x in sonuc):
        raise ValueError("sinyal yalnız sonlu sayılardan oluşmalıdır")
    return sonuc


@dataclass(frozen=True, slots=True)
class BantGecirenAyar:
    alt_kesim_hz: float
    ust_kesim_hz: float
    ornekleme_hz: float
    sira: int = 101

    def dogrula(self) -> None:
        if not all(math.isfinite(x) for x in (
            self.alt_kesim_hz, self.ust_kesim_hz, self.ornekleme_hz
        )):
            raise ValueError("frekanslar sonlu olmalıdır")
        if self.ornekleme_hz <= 0:
            raise ValueError("ornekleme_hz pozitif olmalıdır")
        nyquist = self.ornekleme_hz / 2.0
        if not 0.0 < self.alt_kesim_hz < self.ust_kesim_hz < nyquist:
            raise ValueError("kesim frekansları 0 < alt < üst < Nyquist koşulunu sağlamalıdır")
        if not isinstance(self.sira, int):
            raise TypeError("sıra tam sayı olmalıdır")
        if self.sira < 3:
            raise ValueError("sıra en az 3 olmalıdır")
        if self.sira % 2 == 0:
            raise ValueError("doğrusal faz için sıra tek sayı olmalıdır")


@dataclass(frozen=True, slots=True)
class BantGecirenSonucu:
    cikti: tuple[float, ...]
    katsayilar: tuple[float, ...]
    grup_gecikmesi_ornek: int
    alt_kesim_hz: float
    ust_kesim_hz: float
    ornekleme_hz: float
    yontem: str
    varsayimlar: tuple[str, ...]


class BantGecirenSuzgec:
    """Pencerelenmiş sinc yöntemiyle doğrusal fazlı FIR bant geçiren süzgeç.

    İlk referans çekirdeğidir. Gerçek cihazın analog ön katını veya kalibrasyonunu
    temsil etmez.
    """

    YONTEM = "fir_pencerelenmis_sinc_hamming"
    VARSAYIMLAR = (
        "ornekleme_araligi_sabit",
        "sinyal_dogrusal_zamanla_degisimsiz_suzgecle_uyumlu",
        "kenar_ornekleri_sifir_dolguyla_islenir",
    )

    @staticmethod
    def _dusuk_geciren_katsayilar(kesim_hz: float, ornekleme_hz: float, sira: int) -> list[float]:
        merkez = (sira - 1) / 2.0
        fc = kesim_hz / ornekleme_hz
        katsayilar: list[float] = []
        for n in range(sira):
            k = n - merkez
            if k == 0:
                ideal = 2.0 * fc
            else:
                ideal = math.sin(2.0 * math.pi * fc * k) / (math.pi * k)
            pencere = 0.54 - 0.46 * math.cos(2.0 * math.pi * n / (sira - 1))
            katsayilar.append(ideal * pencere)
        toplam = sum(katsayilar)
        if toplam == 0:
            raise RuntimeError("düşük geçiren katsayı toplamı sıfır olamaz")
        return [x / toplam for x in katsayilar]

    def katsayi_uret(self, ayar: BantGecirenAyar) -> tuple[float, ...]:
        ayar.dogrula()
        ust_lp = self._dusuk_geciren_katsayilar(
            ayar.ust_kesim_hz, ayar.ornekleme_hz, ayar.sira
        )
        alt_lp = self._dusuk_geciren_katsayilar(
            ayar.alt_kesim_hz, ayar.ornekleme_hz, ayar.sira
        )
        return tuple(u - a for u, a in zip(ust_lp, alt_lp))

    def uygula(self, sinyal: Sequence[float], ayar: BantGecirenAyar) -> BantGecirenSonucu:
        girdi = _sonlu_sinyal(sinyal)
        katsayilar = self.katsayi_uret(ayar)
        yarim = (len(katsayilar) - 1) // 2
        cikti: list[float] = []

        for i in range(len(girdi)):
            toplam = 0.0
            for j, h in enumerate(katsayilar):
                kaynak_index = i + j - yarim
                if 0 <= kaynak_index < len(girdi):
                    toplam += girdi[kaynak_index] * h
            cikti.append(toplam)

        return BantGecirenSonucu(
            cikti=tuple(cikti),
            katsayilar=katsayilar,
            grup_gecikmesi_ornek=yarim,
            alt_kesim_hz=ayar.alt_kesim_hz,
            ust_kesim_hz=ayar.ust_kesim_hz,
            ornekleme_hz=ayar.ornekleme_hz,
            yontem=self.YONTEM,
            varsayimlar=self.VARSAYIMLAR,
        )


def bant_gecir(
    sinyal: Sequence[float],
    *,
    alt_kesim_hz: float,
    ust_kesim_hz: float,
    ornekleme_hz: float,
    sira: int = 101,
) -> tuple[float, ...]:
    ayar = BantGecirenAyar(
        alt_kesim_hz=alt_kesim_hz,
        ust_kesim_hz=ust_kesim_hz,
        ornekleme_hz=ornekleme_hz,
        sira=sira,
    )
    return BantGecirenSuzgec().uygula(sinyal, ayar).cikti
