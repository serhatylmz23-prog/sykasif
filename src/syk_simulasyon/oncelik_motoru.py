from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import json


class OneriDurumu(StrEnum):
    ADAY = "aday"
    BILGE_KAAN_INCELEMESI = "bilge_kaan_incelemesi"
    ONAYLANDI = "onaylandi"
    REDDEDILDI = "reddedildi"
    ERTELENDI = "ertelendi"


@dataclass(frozen=True)
class DeneyOnerisi:
    oneri_id: str
    hedef_id: str
    senaryo_ozeti: str
    bilgi_kazanci: float
    belirsizlik_azaltma: float
    tekrar_degeri: float
    hesaplama_maliyeti: float
    risk_puani: float
    kaynak_guveni: float
    durum: OneriDurumu = OneriDurumu.ADAY

    def __post_init__(self) -> None:
        if not self.oneri_id.strip() or not self.hedef_id.strip() or not self.senaryo_ozeti.strip():
            raise ValueError("Öneri kimliği, hedef kimliği ve senaryo özeti zorunludur")
        for alan in (
            self.bilgi_kazanci, self.belirsizlik_azaltma, self.tekrar_degeri,
            self.hesaplama_maliyeti, self.risk_puani, self.kaynak_guveni,
        ):
            if not 0 <= alan <= 1:
                raise ValueError("Öneri puanları 0 ile 1 arasında olmalıdır")

    @property
    def oncelik_puani(self) -> float:
        pozitif = (
            self.bilgi_kazanci * 0.35
            + self.belirsizlik_azaltma * 0.25
            + self.tekrar_degeri * 0.10
            + self.kaynak_guveni * 0.15
        )
        negatif = self.hesaplama_maliyeti * 0.08 + self.risk_puani * 0.07
        return round(max(0.0, min(1.0, pozitif + 0.15 - negatif)), 4)

    @property
    def parmak_izi(self) -> str:
        veri = {"hedef_id": self.hedef_id, "senaryo_ozeti": self.senaryo_ozeti.strip().lower()}
        return sha256(json.dumps(veri, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


@dataclass
class ArastirmaOncelikMotoru:
    gecmis_parmak_izleri: set[str] = field(default_factory=set)

    def tekrar_mi(self, oneri: DeneyOnerisi) -> bool:
        return oneri.parmak_izi in self.gecmis_parmak_izleri

    def kaydet(self, oneri: DeneyOnerisi) -> None:
        self.gecmis_parmak_izleri.add(oneri.parmak_izi)

    def sirala(self, oneriler: list[DeneyOnerisi], en_fazla: int | None = None) -> list[DeneyOnerisi]:
        uygun = [o for o in oneriler if not self.tekrar_mi(o) and o.durum != OneriDurumu.REDDEDILDI]
        uygun.sort(key=lambda o: (-o.oncelik_puani, o.oneri_id))
        return uygun if en_fazla is None else uygun[:en_fazla]

    def bilge_kaan_incelemesine_hazirla(self, oneriler: list[DeneyOnerisi], esik: float = 0.60) -> list[dict]:
        sonuc = []
        for oneri in self.sirala(oneriler):
            if oneri.oncelik_puani >= esik:
                sonuc.append({
                    "oneri_id": oneri.oneri_id,
                    "hedef_id": oneri.hedef_id,
                    "oncelik_puani": oneri.oncelik_puani,
                    "durum": OneriDurumu.BILGE_KAAN_INCELEMESI,
                    "gerekce": "Bilgi kazancı, belirsizlik azaltma, kaynak güveni, maliyet ve risk birlikte değerlendirildi.",
                })
        return sonuc
