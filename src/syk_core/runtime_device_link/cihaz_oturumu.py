"""SyKaşif cihaz bağlantısı oturum modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CihazOturumuHatasi(RuntimeError):
    """Cihaz bağlantı oturumu hatası."""


class OturumDurumu(str, Enum):
    OLUSTURULDU = "oluşturuldu"
    DOGRULANIYOR = "doğrulanıyor"
    BAGLI = "bağlı"
    BEKLIYOR = "bekliyor"
    CEVRIMDISI = "çevrimdışı"
    SONA_ERDI = "sona_erdi"
    REDDEDILDI = "reddedildi"
    HATA = "hata"


@dataclass(slots=True)
class CihazOturumu:
    oturum_kimligi: str
    cihaz_kimligi: str
    baslama_zamani: datetime
    durum: OturumDurumu = (
        OturumDurumu.OLUSTURULDU
    )
    son_canlilik_zamani: datetime | None = None
    son_mesaj_zamani: datetime | None = None
    sona_erme_zamani: datetime | None = None
    gonderilen_mesaj_sayisi: int = 0
    alinan_mesaj_sayisi: int = 0
    reddedilen_mesaj_sayisi: int = 0
    yeniden_baglanma_sayisi: int = 0
    son_sira_numarasi: int = 0
    son_hata: str | None = None
    veri: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.oturum_kimligi.strip():
            raise ValueError(
                "Oturum kimliği boş olamaz."
            )

        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if self.baslama_zamani.tzinfo is None:
            raise ValueError(
                "Başlama zamanı saat dilimi içermelidir."
            )

    @property
    def bagli_mi(self) -> bool:
        return self.durum is OturumDurumu.BAGLI

    @property
    def sona_erdi_mi(self) -> bool:
        return self.durum in {
            OturumDurumu.SONA_ERDI,
            OturumDurumu.REDDEDILDI,
        }

    def sonraki_sira_numarasi(
        self,
    ) -> int:
        self.son_sira_numarasi += 1
        return self.son_sira_numarasi

    def sozluk(self) -> dict[str, Any]:
        return {
            "oturum_kimliği": self.oturum_kimligi,
            "cihaz_kimliği": self.cihaz_kimligi,
            "durum": self.durum.value,
            "başlama_zamanı": (
                self.baslama_zamani.isoformat()
            ),
            "son_canlılık_zamanı": (
                self.son_canlilik_zamani.isoformat()
                if self.son_canlilik_zamani
                else None
            ),
            "son_mesaj_zamanı": (
                self.son_mesaj_zamani.isoformat()
                if self.son_mesaj_zamani
                else None
            ),
            "sona_erme_zamanı": (
                self.sona_erme_zamani.isoformat()
                if self.sona_erme_zamani
                else None
            ),
            "gönderilen_mesaj_sayısı": (
                self.gonderilen_mesaj_sayisi
            ),
            "alınan_mesaj_sayısı": (
                self.alinan_mesaj_sayisi
            ),
            "reddedilen_mesaj_sayısı": (
                self.reddedilen_mesaj_sayisi
            ),
            "yeniden_bağlanma_sayısı": (
                self.yeniden_baglanma_sayisi
            ),
            "son_sıra_numarası": (
                self.son_sira_numarasi
            ),
            "son_hata": self.son_hata,
            "veri": dict(self.veri),
        }
