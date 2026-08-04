"""SyKaşif çalışma terminali veri modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TerminalHatasi(RuntimeError):
    """Çalışma terminali hatası."""


class CihazTuru(str, Enum):
    MASAUSTU = "masaüstü"
    TABLET = "tablet"
    TELEFON = "telefon"
    DIZUSTU = "dizüstü"
    DIGER = "diğer"


class CihazDurumu(str, Enum):
    KAYITLI = "kayıtlı"
    BEKLIYOR = "bekliyor"
    BAGLI = "bağlı"
    CEVRIMDISI = "çevrimdışı"
    ENGELLI = "engelli"
    HATA = "hata"


class YetkiSeviyesi(str, Enum):
    IZLEYICI = "izleyici"
    OPERATOR = "işletmen"
    BILGE_KAAN = "Bilge Kaan"
    KURUCU_KAAN = "Kurucu Kaan"


class KomutTuru(str, Enum):
    UYGULAMA_AC = "uygulamayı_aç"
    UYGULAMA_KAPAT = "uygulamayı_kapat"
    CALISMA_SISTEMINI_BASLAT = "çalışma_sistemini_başlat"
    CALISMA_SISTEMINI_DURDUR = "çalışma_sistemini_durdur"
    MASAUSTUNU_KAPAT = "masaüstünü_kapat"
    MASAUSTUNU_UYANDIR = "masaüstünü_uyandır"
    DURUM_ISTE = "durum_iste"
    BILDIRIM_GONDER = "bildirim_gönder"
    OZEL = "özel"


class KomutDurumu(str, Enum):
    OLUSTURULDU = "oluşturuldu"
    KUYRUKTA = "kuyrukta"
    CALISIYOR = "çalışıyor"
    TAMAMLANDI = "tamamlandı"
    REDDEDILDI = "reddedildi"
    HATA = "hata"
    IPTAL_EDILDI = "iptal_edildi"


class BildirimTuru(str, Enum):
    BILGI = "bilgi"
    BASARILI = "başarılı"
    UYARI = "uyarı"
    HATA = "hata"
    YENI_VERI = "yeni_veri"
    YENI_KANIT = "yeni_kanıt"
    YENI_RAPOR = "yeni_rapor"


@dataclass(slots=True, frozen=True)
class YetkiliCihazTanimi:
    cihaz_kimligi: str
    ad: str
    cihaz_turu: CihazTuru
    yetki_seviyesi: YetkiSeviyesi
    cihaz_parmak_izi: str
    aciklama: str | None = None
    veri: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not self.ad.strip():
            raise ValueError(
                "Cihaz adı boş olamaz."
            )

        if not self.cihaz_parmak_izi.strip():
            raise ValueError(
                "Cihaz parmak izi boş olamaz."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "cihaz_kimliği": self.cihaz_kimligi,
            "ad": self.ad,
            "cihaz_türü": self.cihaz_turu.value,
            "yetki_seviyesi": (
                self.yetki_seviyesi.value
            ),
            "cihaz_parmak_izi": (
                self.cihaz_parmak_izi
            ),
            "açıklama": self.aciklama,
            "veri": dict(self.veri),
        }


@dataclass(slots=True)
class YetkiliCihaz:
    tanim: YetkiliCihazTanimi
    durum: CihazDurumu = CihazDurumu.KAYITLI
    kayit_zamani: datetime | None = None
    son_baglanti_zamani: datetime | None = None
    son_ayrilma_zamani: datetime | None = None
    son_hata: str | None = None
    baglanti_sayisi: int = 0
    gonderilen_komut_sayisi: int = 0
    tamamlanan_komut_sayisi: int = 0
    reddedilen_komut_sayisi: int = 0

    @property
    def bagli_mi(self) -> bool:
        return self.durum is CihazDurumu.BAGLI

    @property
    def engelli_mi(self) -> bool:
        return self.durum is CihazDurumu.ENGELLI

    def sozluk(self) -> dict[str, Any]:
        return {
            **self.tanim.sozluk(),
            "durum": self.durum.value,
            "kayıt_zamanı": (
                self.kayit_zamani.isoformat()
                if self.kayit_zamani
                else None
            ),
            "son_bağlantı_zamanı": (
                self.son_baglanti_zamani.isoformat()
                if self.son_baglanti_zamani
                else None
            ),
            "son_ayrılma_zamanı": (
                self.son_ayrilma_zamani.isoformat()
                if self.son_ayrilma_zamani
                else None
            ),
            "son_hata": self.son_hata,
            "bağlantı_sayısı": self.baglanti_sayisi,
            "gönderilen_komut_sayısı": (
                self.gonderilen_komut_sayisi
            ),
            "tamamlanan_komut_sayısı": (
                self.tamamlanan_komut_sayisi
            ),
            "reddedilen_komut_sayısı": (
                self.reddedilen_komut_sayisi
            ),
        }


@dataclass(slots=True)
class TerminalKomutu:
    komut_kimligi: str
    komut_turu: KomutTuru
    kaynak_cihaz_kimligi: str
    hedef_cihaz_kimligi: str
    olusturulma_zamani: datetime
    durum: KomutDurumu = KomutDurumu.OLUSTURULDU
    icerik: dict[str, Any] = field(
        default_factory=dict
    )
    gerekce: str | None = None
    onaylayan: str | None = None
    calisma_zamani: datetime | None = None
    tamamlanma_zamani: datetime | None = None
    hata: str | None = None
    sonuc: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.komut_kimligi.strip():
            raise ValueError(
                "Komut kimliği boş olamaz."
            )

        if not self.kaynak_cihaz_kimligi.strip():
            raise ValueError(
                "Kaynak cihaz kimliği boş olamaz."
            )

        if not self.hedef_cihaz_kimligi.strip():
            raise ValueError(
                "Hedef cihaz kimliği boş olamaz."
            )

        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "Komut zamanı saat dilimi içermelidir."
            )

    @property
    def sonlandi_mi(self) -> bool:
        return self.durum in {
            KomutDurumu.TAMAMLANDI,
            KomutDurumu.REDDEDILDI,
            KomutDurumu.HATA,
            KomutDurumu.IPTAL_EDILDI,
        }

    def sozluk(self) -> dict[str, Any]:
        return {
            "komut_kimliği": self.komut_kimligi,
            "komut_türü": self.komut_turu.value,
            "kaynak_cihaz_kimliği": (
                self.kaynak_cihaz_kimligi
            ),
            "hedef_cihaz_kimliği": (
                self.hedef_cihaz_kimligi
            ),
            "durum": self.durum.value,
            "içerik": dict(self.icerik),
            "gerekçe": self.gerekce,
            "onaylayan": self.onaylayan,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "çalışma_zamanı": (
                self.calisma_zamani.isoformat()
                if self.calisma_zamani
                else None
            ),
            "tamamlanma_zamanı": (
                self.tamamlanma_zamani.isoformat()
                if self.tamamlanma_zamani
                else None
            ),
            "hata": self.hata,
            "sonuç": dict(self.sonuc),
        }


@dataclass(slots=True, frozen=True)
class TerminalBildirimi:
    bildirim_kimligi: str
    bildirim_turu: BildirimTuru
    baslik: str
    aciklama: str
    olusturulma_zamani: datetime
    hedef_cihaz_kimligi: str | None = None
    kaynak: str = "çalışma_terminali"
    veri: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.baslik.strip():
            raise ValueError(
                "Bildirim başlığı boş olamaz."
            )

        if not self.aciklama.strip():
            raise ValueError(
                "Bildirim açıklaması boş olamaz."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "bildirim_kimliği": (
                self.bildirim_kimligi
            ),
            "bildirim_türü": (
                self.bildirim_turu.value
            ),
            "başlık": self.baslik,
            "açıklama": self.aciklama,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "hedef_cihaz_kimliği": (
                self.hedef_cihaz_kimligi
            ),
            "kaynak": self.kaynak,
            "veri": dict(self.veri),
        }
