"""SyKaşif çalışma terminali güvenli oturum modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class OturumHatasi(RuntimeError):
    """Çalışma terminali oturum hatası."""


class OturumDurumu(str, Enum):
    OLUSTURULDU = "oluşturuldu"
    DOGRULANIYOR = "doğrulanıyor"
    BAGLI = "bağlı"
    BEKLEMEDE = "beklemede"
    CEVRIMDISI = "çevrimdışı"
    SONA_ERDI = "sona_erdi"
    REDDEDILDI = "reddedildi"
    HATA = "hata"


class MesajTuru(str, Enum):
    DURUM = "durum"
    KOMUT = "komut"
    KOMUT_SONUCU = "komut_sonucu"
    BILDIRIM = "bildirim"
    CANLILIK = "canlılık"
    CANLILIK_YANITI = "canlılık_yanıtı"
    VERI = "veri"
    HATA = "hata"


class MesajDurumu(str, Enum):
    OLUSTURULDU = "oluşturuldu"
    IMZALANDI = "imzalandı"
    GONDERILDI = "gönderildi"
    ALINDI = "alındı"
    DOGRULANDI = "doğrulandı"
    REDDEDILDI = "reddedildi"
    ISLENDI = "işlendi"
    HATA = "hata"


@dataclass(slots=True)
class TerminalOturumu:
    oturum_kimligi: str
    cihaz_kimligi: str
    oturum_anahtari: str
    olusturulma_zamani: datetime
    durum: OturumDurumu = OturumDurumu.OLUSTURULDU
    baglanti_zamani: datetime | None = None
    son_canlilik_zamani: datetime | None = None
    son_mesaj_zamani: datetime | None = None
    ayrilma_zamani: datetime | None = None
    sona_erme_zamani: datetime | None = None
    yeniden_baglanma_sayisi: int = 0
    gonderilen_mesaj_sayisi: int = 0
    alinan_mesaj_sayisi: int = 0
    reddedilen_mesaj_sayisi: int = 0
    son_hata: str | None = None
    veri: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.oturum_kimligi.strip():
            raise ValueError(
                "Oturum kimliği boş olamaz."
            )

        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not self.oturum_anahtari.strip():
            raise ValueError(
                "Oturum anahtarı boş olamaz."
            )

        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "Oturum zamanı saat dilimi içermelidir."
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

    def sozluk(self) -> dict[str, Any]:
        return {
            "oturum_kimliği": self.oturum_kimligi,
            "cihaz_kimliği": self.cihaz_kimligi,
            "durum": self.durum.value,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "bağlantı_zamanı": (
                self.baglanti_zamani.isoformat()
                if self.baglanti_zamani
                else None
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
            "ayrılma_zamanı": (
                self.ayrilma_zamani.isoformat()
                if self.ayrilma_zamani
                else None
            ),
            "sona_erme_zamanı": (
                self.sona_erme_zamani.isoformat()
                if self.sona_erme_zamani
                else None
            ),
            "yeniden_bağlanma_sayısı": (
                self.yeniden_baglanma_sayisi
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
            "son_hata": self.son_hata,
            "veri": dict(self.veri),
        }


@dataclass(slots=True)
class TerminalMesaji:
    mesaj_kimligi: str
    oturum_kimligi: str
    kaynak_cihaz_kimligi: str
    hedef_cihaz_kimligi: str
    mesaj_turu: MesajTuru
    sira_numarasi: int
    olusturulma_zamani: datetime
    icerik: dict[str, Any] = field(default_factory=dict)
    durum: MesajDurumu = MesajDurumu.OLUSTURULDU
    imza: str | None = None
    gonderilme_zamani: datetime | None = None
    alinma_zamani: datetime | None = None
    dogrulanma_zamani: datetime | None = None
    islenme_zamani: datetime | None = None
    hata: str | None = None

    def __post_init__(self) -> None:
        if not self.mesaj_kimligi.strip():
            raise ValueError(
                "Mesaj kimliği boş olamaz."
            )

        if not self.oturum_kimligi.strip():
            raise ValueError(
                "Oturum kimliği boş olamaz."
            )

        if not self.kaynak_cihaz_kimligi.strip():
            raise ValueError(
                "Kaynak cihaz kimliği boş olamaz."
            )

        if not self.hedef_cihaz_kimligi.strip():
            raise ValueError(
                "Hedef cihaz kimliği boş olamaz."
            )

        if self.sira_numarasi <= 0:
            raise ValueError(
                "Mesaj sıra numarası sıfırdan büyük olmalıdır."
            )

        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "Mesaj zamanı saat dilimi içermelidir."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "mesaj_kimliği": self.mesaj_kimligi,
            "oturum_kimliği": self.oturum_kimligi,
            "kaynak_cihaz_kimliği": (
                self.kaynak_cihaz_kimligi
            ),
            "hedef_cihaz_kimliği": (
                self.hedef_cihaz_kimligi
            ),
            "mesaj_türü": self.mesaj_turu.value,
            "sıra_numarası": self.sira_numarasi,
            "durum": self.durum.value,
            "içerik": dict(self.icerik),
            "imza": self.imza,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "gönderilme_zamanı": (
                self.gonderilme_zamani.isoformat()
                if self.gonderilme_zamani
                else None
            ),
            "alınma_zamanı": (
                self.alinma_zamani.isoformat()
                if self.alinma_zamani
                else None
            ),
            "doğrulanma_zamanı": (
                self.dogrulanma_zamani.isoformat()
                if self.dogrulanma_zamani
                else None
            ),
            "işlenme_zamanı": (
                self.islenme_zamani.isoformat()
                if self.islenme_zamani
                else None
            ),
            "hata": self.hata,
        }
