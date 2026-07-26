from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from itertools import product
from math import isfinite
from typing import Iterable


class HedefAnaSinifi(StrEnum):
    MALZEME = "malzeme"
    MINERAL = "mineral"
    BOSLUK = "bosluk"
    GEOMETRIK_YAPI = "geometrik_yapi"
    KAYA_YAPISI = "kaya_yapisi"
    YUZEY_ANOMALISI = "yuzey_anomalisi"


class KanitTuru(StrEnum):
    LITERATUR = "literatur"
    SIMULASYON = "simulasyon"
    UZMAN_ONERISI = "uzman_onerisi"
    SAHA_GERI_BESLEMESI = "saha_geri_beslemesi"


@dataclass(frozen=True)
class HedefTanim:
    ana_sinif: HedefAnaSinifi
    alt_sinif: str
    malzeme_ozellikleri: dict[str, float | str] = field(default_factory=dict)
    geometri: str = "belirsiz"
    boyut_m: tuple[float, float, float] | None = None
    yonelim_derece: float | None = None

    def __post_init__(self) -> None:
        if not self.alt_sinif.strip():
            raise ValueError("Alt sınıf boş olamaz")
        if self.boyut_m is not None and any(v <= 0 or not isfinite(v) for v in self.boyut_m):
            raise ValueError("Hedef boyutları pozitif ve sonlu olmalıdır")
        if self.yonelim_derece is not None and not 0 <= self.yonelim_derece < 360:
            raise ValueError("Yönelim 0 dahil, 360 hariç derece aralığında olmalıdır")


@dataclass(frozen=True)
class OrtamTanim:
    ortam_turu: str
    nem_orani: float
    sicaklik_c: float
    iletkenlik_s_m: float | None = None
    gurultu_puani: float = 0.0

    def __post_init__(self) -> None:
        if not 0 <= self.nem_orani <= 1:
            raise ValueError("Nem oranı 0 ile 1 arasında olmalıdır")
        if not 0 <= self.gurultu_puani <= 1:
            raise ValueError("Gürültü puanı 0 ile 1 arasında olmalıdır")
        if self.iletkenlik_s_m is not None and self.iletkenlik_s_m < 0:
            raise ValueError("İletkenlik negatif olamaz")


@dataclass(frozen=True)
class FrekansOnerisi:
    sensor_ailesi: str
    alt_frekans_hz: float
    ust_frekans_hz: float
    adim_hz: float
    yayilim_hizi_m_s: float
    gerekce: str
    kaynak_turu: KanitTuru
    kaynak_kimligi: str
    bilge_kaan_onay_kimligi: str | None = None

    def __post_init__(self) -> None:
        if self.alt_frekans_hz <= 0 or self.ust_frekans_hz < self.alt_frekans_hz:
            raise ValueError("Frekans aralığı geçersiz")
        if self.adim_hz <= 0 or self.yayilim_hizi_m_s <= 0:
            raise ValueError("Frekans adımı ve yayılım hızı pozitif olmalıdır")
        if not self.gerekce.strip() or not self.kaynak_kimligi.strip():
            raise ValueError("Frekans önerisi gerekçe ve kaynak içermelidir")

    @property
    def bilge_kaan_onayli(self) -> bool:
        return bool(self.bilge_kaan_onay_kimligi)

    def frekanslar(self) -> tuple[float, ...]:
        if not self.bilge_kaan_onayli:
            raise PermissionError("Frekans matrisi Bilge Kaan onayı olmadan üretilemez")
        sonuc: list[float] = []
        deger = self.alt_frekans_hz
        while deger <= self.ust_frekans_hz + self.adim_hz * 1e-9:
            sonuc.append(round(deger, 9))
            deger += self.adim_hz
        return tuple(sonuc)

    def dalga_boyu_m(self, frekans_hz: float) -> float:
        if not self.bilge_kaan_onayli:
            raise PermissionError("Dalga boyu Bilge Kaan onayı olmadan kesinleştirilemez")
        if not self.alt_frekans_hz <= frekans_hz <= self.ust_frekans_hz:
            raise ValueError("Frekans onaylı aralığın dışında")
        return self.yayilim_hizi_m_s / frekans_hz


@dataclass(frozen=True)
class DerinlikPlani:
    temel_ust_sinir_m: float = 2.0
    deneysel_ust_sinir_m: float = 2.25
    temel_noktalar_m: tuple[float, ...] = (
        0.05, 0.10, 0.15, 0.20,
        0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00,
        1.25, 1.50, 1.75, 2.00,
    )

    def dogrula(self, derinlik_m: float, deneysel: bool = False) -> None:
        ust = self.deneysel_ust_sinir_m if deneysel else self.temel_ust_sinir_m
        if derinlik_m <= 0 or derinlik_m > ust:
            tur = "deneysel" if deneysel else "temel"
            raise ValueError(f"Derinlik {tur} sınırın dışında: 0 < derinlik <= {ust}")

    def rastgele_noktalari_dogrula(self, noktalar: Iterable[float]) -> tuple[float, ...]:
        sonuc = tuple(float(v) for v in noktalar)
        for v in sonuc:
            self.dogrula(v)
        return sonuc


@dataclass(frozen=True)
class DeneySenaryosu:
    hedef: HedefTanim
    ortam: OrtamTanim
    derinlik_m: float
    frekans_hz: float
    dalga_boyu_m: float
    deneysel_derinlik: bool = False


@dataclass
class SimulasyonDeneyMatrisi:
    derinlik_plani: DerinlikPlani = field(default_factory=DerinlikPlani)

    def uret(
        self,
        hedefler: Iterable[HedefTanim],
        ortamlar: Iterable[OrtamTanim],
        frekans_onerisi: FrekansOnerisi,
        derinlikler_m: Iterable[float] | None = None,
        deneysel_derinlik: bool = False,
    ) -> list[DeneySenaryosu]:
        frekanslar = frekans_onerisi.frekanslar()
        derinlikler = tuple(derinlikler_m or self.derinlik_plani.temel_noktalar_m)
        for derinlik in derinlikler:
            self.derinlik_plani.dogrula(derinlik, deneysel=deneysel_derinlik)

        senaryolar: list[DeneySenaryosu] = []
        for hedef, ortam, derinlik, frekans in product(tuple(hedefler), tuple(ortamlar), derinlikler, frekanslar):
            senaryolar.append(
                DeneySenaryosu(
                    hedef=hedef,
                    ortam=ortam,
                    derinlik_m=derinlik,
                    frekans_hz=frekans,
                    dalga_boyu_m=frekans_onerisi.dalga_boyu_m(frekans),
                    deneysel_derinlik=deneysel_derinlik,
                )
            )
        return senaryolar
