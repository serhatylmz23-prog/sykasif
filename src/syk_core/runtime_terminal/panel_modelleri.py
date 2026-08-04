"""SyKaşif terminal paneli modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PanelHatasi(RuntimeError):
    """Terminal paneli hatası."""


class PanelDurumu(str, Enum):
    HAZIRLANIYOR = "hazırlanıyor"
    HAZIR = "hazır"
    CALISIYOR = "çalışıyor"
    BEKLIYOR = "bekliyor"
    CEVRIMDISI = "çevrimdışı"
    HATA = "hata"


class PanelBolumu(str, Enum):
    GENEL_DURUM = "genel_durum"
    YETKILI_CIHAZLAR = "yetkili_cihazlar"
    OTURUMLAR = "oturumlar"
    KOMUTLAR = "komutlar"
    BILDIRIMLER = "bildirimler"
    SISTEM_SAGLIGI = "sistem_sağlığı"


@dataclass(slots=True, frozen=True)
class PanelAyarlari:
    baslik: str = "SyKaşif Terminali"
    alt_baslik: str = "Yetkili cihaz ve çalışma sistemi yönetimi"
    yenileme_suresi_saniye: int = 5
    en_fazla_komut_sayisi: int = 20
    en_fazla_bildirim_sayisi: int = 20
    en_fazla_oturum_sayisi: int = 20
    koyu_gorunum: bool = True
    veri: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.baslik.strip():
            raise ValueError(
                "Panel başlığı boş olamaz."
            )

        if not self.alt_baslik.strip():
            raise ValueError(
                "Panel alt başlığı boş olamaz."
            )

        if self.yenileme_suresi_saniye <= 0:
            raise ValueError(
                "Yenileme süresi sıfırdan büyük olmalıdır."
            )

        if self.en_fazla_komut_sayisi <= 0:
            raise ValueError(
                "Komut gösterim sınırı sıfırdan büyük olmalıdır."
            )

        if self.en_fazla_bildirim_sayisi <= 0:
            raise ValueError(
                "Bildirim gösterim sınırı sıfırdan büyük olmalıdır."
            )

        if self.en_fazla_oturum_sayisi <= 0:
            raise ValueError(
                "Oturum gösterim sınırı sıfırdan büyük olmalıdır."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "başlık": self.baslik,
            "alt_başlık": self.alt_baslik,
            "yenileme_süresi_saniye": (
                self.yenileme_suresi_saniye
            ),
            "en_fazla_komut_sayısı": (
                self.en_fazla_komut_sayisi
            ),
            "en_fazla_bildirim_sayısı": (
                self.en_fazla_bildirim_sayisi
            ),
            "en_fazla_oturum_sayısı": (
                self.en_fazla_oturum_sayisi
            ),
            "koyu_görünüm": self.koyu_gorunum,
            "veri": dict(self.veri),
        }


@dataclass(slots=True)
class PanelAnlikGorunumu:
    olusturulma_zamani: datetime
    panel_durumu: PanelDurumu
    toplam_cihaz_sayisi: int
    bagli_cihaz_sayisi: int
    cevrimdisi_cihaz_sayisi: int
    engelli_cihaz_sayisi: int
    etkin_oturum_sayisi: int
    kuyruktaki_komut_sayisi: int
    tamamlanan_komut_sayisi: int
    reddedilen_komut_sayisi: int
    bildirim_sayisi: int
    cihazlar: list[dict[str, Any]] = field(
        default_factory=list
    )
    oturumlar: list[dict[str, Any]] = field(
        default_factory=list
    )
    komutlar: list[dict[str, Any]] = field(
        default_factory=list
    )
    bildirimler: list[dict[str, Any]] = field(
        default_factory=list
    )
    sistem: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "Panel görünümü zamanı saat dilimi içermelidir."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "panel_durumu": self.panel_durumu.value,
            "toplam_cihaz_sayısı": (
                self.toplam_cihaz_sayisi
            ),
            "bağlı_cihaz_sayısı": (
                self.bagli_cihaz_sayisi
            ),
            "çevrimdışı_cihaz_sayısı": (
                self.cevrimdisi_cihaz_sayisi
            ),
            "engelli_cihaz_sayısı": (
                self.engelli_cihaz_sayisi
            ),
            "etkin_oturum_sayısı": (
                self.etkin_oturum_sayisi
            ),
            "kuyruktaki_komut_sayısı": (
                self.kuyruktaki_komut_sayisi
            ),
            "tamamlanan_komut_sayısı": (
                self.tamamlanan_komut_sayisi
            ),
            "reddedilen_komut_sayısı": (
                self.reddedilen_komut_sayisi
            ),
            "bildirim_sayısı": (
                self.bildirim_sayisi
            ),
            "cihazlar": list(self.cihazlar),
            "oturumlar": list(self.oturumlar),
            "komutlar": list(self.komutlar),
            "bildirimler": list(self.bildirimler),
            "sistem": dict(self.sistem),
        }
