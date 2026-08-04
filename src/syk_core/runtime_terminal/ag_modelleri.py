"""SyKaşif terminal ağ geçidi veri modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgGecidiHatasi(RuntimeError):
    """Terminal ağ geçidi hatası."""


class IstekDurumu(str, Enum):
    ALINDI = "alındı"
    DOGRULANDI = "doğrulandı"
    ISLENDI = "işlendi"
    REDDEDILDI = "reddedildi"
    HATA = "hata"


class IstekTuru(str, Enum):
    CIHAZ_KAYDI = "cihaz_kaydı"
    OTURUM_ACMA = "oturum_açma"
    CANLILIK = "canlılık"
    DURUM = "durum"
    KOMUT = "komut"
    BILDIRIM = "bildirim"
    OTURUM_KAPATMA = "oturum_kapatma"


@dataclass(slots=True)
class AgIstegi:
    istek_kimligi: str
    istek_turu: IstekTuru
    olusturulma_zamani: datetime
    kaynak_adres: str | None = None
    cihaz_kimligi: str | None = None
    oturum_kimligi: str | None = None
    durum: IstekDurumu = IstekDurumu.ALINDI
    icerik: dict[str, Any] = field(default_factory=dict)
    sonuc: dict[str, Any] = field(default_factory=dict)
    hata: str | None = None
    tamamlanma_zamani: datetime | None = None

    def __post_init__(self) -> None:
        if not self.istek_kimligi.strip():
            raise ValueError(
                "İstek kimliği boş olamaz."
            )

        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "İstek zamanı saat dilimi içermelidir."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "istek_kimliği": self.istek_kimligi,
            "istek_türü": self.istek_turu.value,
            "kaynak_adres": self.kaynak_adres,
            "cihaz_kimliği": self.cihaz_kimligi,
            "oturum_kimliği": self.oturum_kimligi,
            "durum": self.durum.value,
            "içerik": dict(self.icerik),
            "sonuç": dict(self.sonuc),
            "hata": self.hata,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "tamamlanma_zamanı": (
                self.tamamlanma_zamani.isoformat()
                if self.tamamlanma_zamani
                else None
            ),
        }


@dataclass(slots=True, frozen=True)
class AgGecidiAyarlari:
    ana_makine: str = "127.0.0.1"
    baglanti_noktasi: int = 8014
    dis_ag_erisimine_izin_ver: bool = False
    istek_gecmisi_siniri: int = 2000
    en_fazla_icerik_bayti: int = 1_048_576
    oturum_anahtarini_yanitta_goster: bool = False

    def __post_init__(self) -> None:
        if not self.ana_makine.strip():
            raise ValueError(
                "Ana makine adresi boş olamaz."
            )

        if not 1 <= self.baglanti_noktasi <= 65535:
            raise ValueError(
                "Bağlantı noktası 1 ile 65535 arasında olmalıdır."
            )

        if self.istek_gecmisi_siniri <= 0:
            raise ValueError(
                "İstek geçmişi sınırı sıfırdan büyük olmalıdır."
            )

        if self.en_fazla_icerik_bayti <= 0:
            raise ValueError(
                "En fazla içerik boyutu sıfırdan büyük olmalıdır."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "ana_makine": self.ana_makine,
            "bağlantı_noktası": self.baglanti_noktasi,
            "dış_ağ_erişimine_izin_ver": (
                self.dis_ag_erisimine_izin_ver
            ),
            "istek_geçmişi_sınırı": (
                self.istek_gecmisi_siniri
            ),
            "en_fazla_içerik_baytı": (
                self.en_fazla_icerik_bayti
            ),
            "oturum_anahtarını_yanıtta_göster": (
                self.oturum_anahtarini_yanitta_goster
            ),
        }
