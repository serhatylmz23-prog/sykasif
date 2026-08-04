"""SyKaşif yetkili cihaz aracısı modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CihazAraciHatasi(RuntimeError):
    """Yetkili cihaz aracısı hatası."""


class AracDurumu(str, Enum):
    HAZIRLANIYOR = "hazırlanıyor"
    HAZIR = "hazır"
    CALISIYOR = "çalışıyor"
    DURDURULDU = "durduruldu"
    CEVRIMDISI = "çevrimdışı"
    HATA = "hata"


class IslemTuru(str, Enum):
    DURUM_BILGISI = "durum_bilgisi"
    UYGULAMA_AC = "uygulamayı_aç"
    UYGULAMA_KAPAT = "uygulamayı_kapat"
    CALISMA_SISTEMINI_BASLAT = "çalışma_sistemini_başlat"
    CALISMA_SISTEMINI_DURDUR = "çalışma_sistemini_durdur"
    MASAUSTUNU_KAPAT = "masaüstünü_kapat"
    MASAUSTUNU_UYANDIR = "masaüstünü_uyandır"
    GUVENLI_YENIDEN_BASLAT = "güvenli_yeniden_başlat"


class IslemDurumu(str, Enum):
    BEKLIYOR = "bekliyor"
    DOGRULANDI = "doğrulandı"
    CALISIYOR = "çalışıyor"
    TAMAMLANDI = "tamamlandı"
    REDDEDILDI = "reddedildi"
    HATA = "hata"


@dataclass(slots=True, frozen=True)
class UygulamaTanimi:
    uygulama_kimligi: str
    gorunen_ad: str
    calistirma_yolu: str
    calistirma_degiskenleri: tuple[str, ...] = ()
    guvenli_kapatma_destegi: bool = True
    aciklama: str | None = None
    veri: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.uygulama_kimligi.strip():
            raise ValueError(
                "Uygulama kimliği boş olamaz."
            )

        if not self.gorunen_ad.strip():
            raise ValueError(
                "Uygulama adı boş olamaz."
            )

        if not self.calistirma_yolu.strip():
            raise ValueError(
                "Uygulama çalıştırma yolu boş olamaz."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "uygulama_kimliği": self.uygulama_kimligi,
            "görünen_ad": self.gorunen_ad,
            "çalıştırma_yolu": self.calistirma_yolu,
            "çalıştırma_değişkenleri": list(
                self.calistirma_degiskenleri
            ),
            "güvenli_kapatma_desteği": (
                self.guvenli_kapatma_destegi
            ),
            "açıklama": self.aciklama,
            "veri": dict(self.veri),
        }


@dataclass(slots=True)
class UygulamaDurumu:
    uygulama_kimligi: str
    calisiyor_mu: bool = False
    islem_kimligi: int | None = None
    baslama_zamani: datetime | None = None
    kapanma_zamani: datetime | None = None
    son_hata: str | None = None
    baslatma_sayisi: int = 0
    kapatma_sayisi: int = 0

    def sozluk(self) -> dict[str, Any]:
        return {
            "uygulama_kimliği": self.uygulama_kimligi,
            "çalışıyor_mu": self.calisiyor_mu,
            "işlem_kimliği": self.islem_kimligi,
            "başlama_zamanı": (
                self.baslama_zamani.isoformat()
                if self.baslama_zamani
                else None
            ),
            "kapanma_zamanı": (
                self.kapanma_zamani.isoformat()
                if self.kapanma_zamani
                else None
            ),
            "son_hata": self.son_hata,
            "başlatma_sayısı": self.baslatma_sayisi,
            "kapatma_sayısı": self.kapatma_sayisi,
        }


@dataclass(slots=True)
class AracIslemi:
    islem_kimligi: str
    islem_turu: IslemTuru
    kaynak_cihaz_kimligi: str
    olusturulma_zamani: datetime
    durum: IslemDurumu = IslemDurumu.BEKLIYOR
    uygulama_kimligi: str | None = None
    insan_onayi: str | None = None
    gerekce: str | None = None
    icerik: dict[str, Any] = field(default_factory=dict)
    baslama_zamani: datetime | None = None
    tamamlanma_zamani: datetime | None = None
    sonuc: dict[str, Any] = field(default_factory=dict)
    hata: str | None = None

    def __post_init__(self) -> None:
        if not self.islem_kimligi.strip():
            raise ValueError(
                "İşlem kimliği boş olamaz."
            )

        if not self.kaynak_cihaz_kimligi.strip():
            raise ValueError(
                "Kaynak cihaz kimliği boş olamaz."
            )

        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "İşlem zamanı saat dilimi içermelidir."
            )

    @property
    def sonlandi_mi(self) -> bool:
        return self.durum in {
            IslemDurumu.TAMAMLANDI,
            IslemDurumu.REDDEDILDI,
            IslemDurumu.HATA,
        }

    def sozluk(self) -> dict[str, Any]:
        return {
            "işlem_kimliği": self.islem_kimligi,
            "işlem_türü": self.islem_turu.value,
            "kaynak_cihaz_kimliği": (
                self.kaynak_cihaz_kimligi
            ),
            "uygulama_kimliği": self.uygulama_kimligi,
            "durum": self.durum.value,
            "insan_onayı": self.insan_onayi,
            "gerekçe": self.gerekce,
            "içerik": dict(self.icerik),
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "başlama_zamanı": (
                self.baslama_zamani.isoformat()
                if self.baslama_zamani
                else None
            ),
            "tamamlanma_zamanı": (
                self.tamamlanma_zamani.isoformat()
                if self.tamamlanma_zamani
                else None
            ),
            "sonuç": dict(self.sonuc),
            "hata": self.hata,
        }
