from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

class Karar(StrEnum):
    ONAY = "onay"
    RED = "red"
    EK_VERI = "ek_veri"
    GUVENLI_DURDUR = "guvenli_durdur"

YASAK_AMACLAR = {
    "istihbarat", "milli_guvenlik", "yetkisiz_gozetim", "canli_insan_takibi",
    "yuz_tanima", "kimliklendirme", "gizli_devlet_faaliyeti"
}

@dataclass(frozen=True)
class ParametreSiniri:
    ad: str
    alt: float
    ust: float
    birim: str

    def kapsar(self, deger: float) -> bool:
        return self.alt <= deger <= self.ust

@dataclass
class BilgeKaanKontrolluOtonom:
    sinirlar: dict[str, ParametreSiniri]
    aktif: bool = True
    olay_kaydi: list[dict[str, Any]] = field(default_factory=list)

    def degerlendir(self, amac: str, degisiklikler: dict[str, float]) -> Karar:
        if amac in YASAK_AMACLAR:
            self.aktif = False
            self.olay_kaydi.append({"karar": Karar.GUVENLI_DURDUR, "gerekce": "Tartışmaya kapalı yasak kullanım alanı"})
            return Karar.GUVENLI_DURDUR
        for ad, deger in degisiklikler.items():
            sinir = self.sinirlar.get(ad)
            if sinir is None:
                self.olay_kaydi.append({"karar": Karar.EK_VERI, "gerekce": f"{ad} için onaylı sınır yok"})
                return Karar.EK_VERI
            if not sinir.kapsar(deger):
                self.olay_kaydi.append({"karar": Karar.EK_VERI, "gerekce": f"{ad} onaylı sınır dışında"})
                return Karar.EK_VERI
        self.olay_kaydi.append({"karar": Karar.ONAY, "gerekce": "Tüm değişiklikler Bilge Kaan onaylı sınırlar içinde"})
        return Karar.ONAY

@dataclass
class KurucuKaanKontrolluOtonom:
    def kalici_terfi_karari(self, bilge_karari: Karar, kanit_puani: float, geri_alma_plani_var: bool) -> Karar:
        if bilge_karari != Karar.ONAY:
            return Karar.RED
        if kanit_puani < 0.80 or not geri_alma_plani_var:
            return Karar.EK_VERI
        return Karar.ONAY

@dataclass(frozen=True)
class BilgeKaanTeknikOnayi:
    onay_kimligi: str
    konu: str
    gerekce: str
    kanit_kimlikleri: tuple[str, ...]
    onaylayan: str = "Bilge Kaan Kontrollü Otonom"

    def __post_init__(self) -> None:
        if not self.onay_kimligi.strip() or not self.konu.strip() or not self.gerekce.strip():
            raise ValueError("Teknik onay kimliği, konusu ve gerekçesi zorunludur")
        if not self.kanit_kimlikleri:
            raise ValueError("Teknik onay en az bir kanıta dayanmalıdır")
