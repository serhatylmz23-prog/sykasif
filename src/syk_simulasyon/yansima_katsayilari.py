from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class KatsayiDurumu(StrEnum):
    DOGRULANMIS = "dogrulanmis"
    REFERANS = "referans"
    VERI_YETERSIZ = "veri_yetersiz"


@dataclass(frozen=True, slots=True)
class YansimaKatsayiKaydi:
    katsayi_kimligi: str
    genlik_katsayisi: float | None
    kaynak: str | None
    guven_0_1: float
    durum: KatsayiDurumu
    frekans_alt_hz: float | None = None
    frekans_ust_hz: float | None = None

    def dogrula(self, frekans_hz: float) -> None:
        if not self.katsayi_kimligi.strip():
            raise ValueError("katsayi_kimligi boş olamaz")
        if frekans_hz <= 0:
            raise ValueError("frekans_hz pozitif olmalıdır")
        if not 0.0 <= self.guven_0_1 <= 1.0:
            raise ValueError("guven_0_1 0 ile 1 arasında olmalıdır")
        if self.durum is KatsayiDurumu.VERI_YETERSIZ:
            raise ValueError("yansıma katsayısı için veri yetersiz")
        if self.genlik_katsayisi is None or not 0.0 <= self.genlik_katsayisi <= 1.0:
            raise ValueError("genlik_katsayisi 0 ile 1 arasında olmalıdır")
        if not self.kaynak:
            raise ValueError("katsayı kaynağı zorunludur")
        if self.frekans_alt_hz is not None and frekans_hz < self.frekans_alt_hz:
            raise ValueError("frekans katsayı aralığının altındadır")
        if self.frekans_ust_hz is not None and frekans_hz > self.frekans_ust_hz:
            raise ValueError("frekans katsayı aralığının üstündedir")
