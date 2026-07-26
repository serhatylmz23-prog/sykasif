from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Iterable
import json
import uuid


class BilgiDurumu(StrEnum):
    TASLAK = "taslak"
    DOGRULANIYOR = "dogrulaniyor"
    KULLANIMDA = "kullanimda"
    YENIDEN_DOGRULAMA_GEREKLI = "yeniden_dogrulama_gerekli"
    ARSIV = "arsiv"
    GECERSIZ = "gecersiz"


class HataTuru(StrEnum):
    VERI = "veri"
    SENSOR = "sensor"
    SIMULASYON = "simulasyon"
    PARAMETRE = "parametre"
    GORSEL = "gorsel"
    ILETISIM = "iletisim"
    YETKI = "yetki"
    DIGER = "diger"


@dataclass(frozen=True)
class GuvenKaydi:
    puan: float
    gerekce: str
    zaman: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not 0.0 <= self.puan <= 1.0:
            raise ValueError("Güven puanı 0 ile 1 arasında olmalıdır")
        if not self.gerekce.strip():
            raise ValueError("Güven gerekçesi boş olamaz")


@dataclass
class BilgiKaydi:
    baslik: str
    icerik_ozeti: str
    kaynak_kimlikleri: tuple[str, ...]
    durum: BilgiDurumu = BilgiDurumu.TASLAK
    tekrar_sayisi: int = 0
    bagimsiz_dogrulandi: bool = False
    simulasyonla_uyumlu: bool | None = None
    sahayla_uyumlu: bool | None = None
    son_inceleme: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    gecerlilik_suresi_gun: int = 180
    bilgi_id: str = field(default_factory=lambda: f"BK-{uuid.uuid4().hex[:16].upper()}")
    guven_gecmisi: list[GuvenKaydi] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.baslik.strip() or not self.icerik_ozeti.strip():
            raise ValueError("Başlık ve içerik özeti boş olamaz")
        if self.gecerlilik_suresi_gun < 1:
            raise ValueError("Geçerlilik süresi en az bir gün olmalıdır")
        if self.tekrar_sayisi < 0:
            raise ValueError("Tekrar sayısı negatif olamaz")

    @property
    def guncel_guven(self) -> float:
        return self.guven_gecmisi[-1].puan if self.guven_gecmisi else 0.0

    def guven_ekle(self, puan: float, gerekce: str, zaman: datetime | None = None) -> None:
        self.guven_gecmisi.append(GuvenKaydi(puan, gerekce, zaman or datetime.now(timezone.utc)))

    def eskidi_mi(self, simdi: datetime | None = None) -> bool:
        simdi = simdi or datetime.now(timezone.utc)
        return simdi > self.son_inceleme + timedelta(days=self.gecerlilik_suresi_gun)

    def yeniden_dogrulama_durumu(self, simdi: datetime | None = None, yeni_kaynak_var: bool = False) -> bool:
        gerekli = self.eskidi_mi(simdi) or yeni_kaynak_var
        if gerekli and self.durum not in {BilgiDurumu.GECERSIZ, BilgiDurumu.ARSIV}:
            self.durum = BilgiDurumu.YENIDEN_DOGRULAMA_GEREKLI
        return gerekli

    def guven_zinciri_puani(self) -> float:
        puan = self.guncel_guven
        puan += min(0.12, self.tekrar_sayisi * 0.03)
        puan += 0.10 if self.bagimsiz_dogrulandi else 0.0
        puan += 0.05 if self.simulasyonla_uyumlu is True else 0.0
        puan += 0.10 if self.sahayla_uyumlu is True else 0.0
        if self.simulasyonla_uyumlu is False:
            puan -= 0.15
        if self.sahayla_uyumlu is False:
            puan -= 0.25
        if not self.kaynak_kimlikleri:
            puan -= 0.20
        return round(max(0.0, min(1.0, puan)), 4)

    def icerik_parmak_izi(self) -> str:
        veri = {
            "baslik": self.baslik,
            "icerik_ozeti": self.icerik_ozeti,
            "kaynak_kimlikleri": sorted(self.kaynak_kimlikleri),
        }
        return sha256(json.dumps(veri, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class BilgiCatismasi:
    birinci_bilgi_id: str
    ikinci_bilgi_id: str
    konu: str
    fark_ozeti: str
    olasi_nedenler: tuple[str, ...] = ()
    tekrar_deneyleri: tuple[str, ...] = ()
    catisma_id: str = field(default_factory=lambda: f"BC-{uuid.uuid4().hex[:16].upper()}")

    def __post_init__(self) -> None:
        if self.birinci_bilgi_id == self.ikinci_bilgi_id:
            raise ValueError("Bir bilgi kaydı kendisiyle çatışamaz")
        if not self.konu.strip() or not self.fark_ozeti.strip():
            raise ValueError("Çatışma konusu ve fark özeti boş olamaz")


@dataclass
class HataKaydi:
    hata_turu: HataTuru
    aciklama: str
    baglam: dict[str, str]
    tekrar_onleme_onerisi: str
    kaynak_deney_no: str | None = None
    hata_id: str = field(default_factory=lambda: f"HH-{uuid.uuid4().hex[:16].upper()}")
    tekrar_sayisi: int = 1
    son_gorulme: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.aciklama.strip() or not self.tekrar_onleme_onerisi.strip():
            raise ValueError("Hata açıklaması ve tekrar önleme önerisi boş olamaz")
        if self.tekrar_sayisi < 1:
            raise ValueError("Tekrar sayısı en az bir olmalıdır")

    def ayni_hata_mi(self, diger: "HataKaydi") -> bool:
        return (
            self.hata_turu == diger.hata_turu
            and self.aciklama.casefold().strip() == diger.aciklama.casefold().strip()
            and self.baglam == diger.baglam
        )


class HataHafizasi:
    def __init__(self) -> None:
        self._kayitlar: list[HataKaydi] = []

    def kaydet(self, hata: HataKaydi) -> HataKaydi:
        for mevcut in self._kayitlar:
            if mevcut.ayni_hata_mi(hata):
                mevcut.tekrar_sayisi += 1
                mevcut.son_gorulme = hata.son_gorulme
                return mevcut
        self._kayitlar.append(hata)
        return hata

    def benzer_hatalar(self, hata_turu: HataTuru, en_az_tekrar: int = 1) -> tuple[HataKaydi, ...]:
        return tuple(k for k in self._kayitlar if k.hata_turu == hata_turu and k.tekrar_sayisi >= en_az_tekrar)

    def deney_icin_uyarilar(self, baglam: dict[str, str]) -> tuple[str, ...]:
        uyarilar: list[str] = []
        for kayit in self._kayitlar:
            ortak = set(kayit.baglam.items()) & set(baglam.items())
            if ortak:
                uyarilar.append(kayit.tekrar_onleme_onerisi)
        return tuple(dict.fromkeys(uyarilar))


@dataclass(frozen=True)
class YasamDongusuKarari:
    bilgi_id: str
    onerilen_durum: BilgiDurumu
    gerekce: str
    bilge_kaan_onayi: bool
    kurucu_kaan_onayi: bool = False


def durum_gecisi_uygula(kayit: BilgiKaydi, karar: YasamDongusuKarari) -> BilgiKaydi:
    if karar.bilgi_id != kayit.bilgi_id:
        raise ValueError("Karar ile bilgi kimliği uyuşmuyor")
    if not karar.bilge_kaan_onayi:
        raise PermissionError("Bilge Kaan onayı olmadan yaşam durumu değiştirilemez")
    kalici_durumlar = {BilgiDurumu.ARSIV, BilgiDurumu.GECERSIZ}
    if karar.onerilen_durum in kalici_durumlar and not karar.kurucu_kaan_onayi:
        raise PermissionError("Arşiv veya geçersiz kararı için Kurucu Kaan onayı gerekir")
    kayit.durum = karar.onerilen_durum
    kayit.son_inceleme = datetime.now(timezone.utc)
    return kayit


def catismalari_bul(kayitlar: Iterable[BilgiKaydi], guven_farki_esigi: float = 0.30) -> tuple[BilgiCatismasi, ...]:
    liste = list(kayitlar)
    sonuclar: list[BilgiCatismasi] = []
    for i, birinci in enumerate(liste):
        for ikinci in liste[i + 1:]:
            if birinci.baslik.casefold().strip() != ikinci.baslik.casefold().strip():
                continue
            fark = abs(birinci.guven_zinciri_puani() - ikinci.guven_zinciri_puani())
            icerik_farkli = birinci.icerik_parmak_izi() != ikinci.icerik_parmak_izi()
            saha_celiskisi = birinci.sahayla_uyumlu is not None and ikinci.sahayla_uyumlu is not None and birinci.sahayla_uyumlu != ikinci.sahayla_uyumlu
            if icerik_farkli and (fark >= guven_farki_esigi or saha_celiskisi):
                sonuclar.append(BilgiCatismasi(
                    birinci.bilgi_id,
                    ikinci.bilgi_id,
                    birinci.baslik,
                    f"Güven farkı {fark:.2f}; içerik veya doğrulama durumu uyuşmuyor.",
                    ("ortam farkı", "sensör farkı", "veri sürümü farkı"),
                    ("aynı koşullarda tekrar deney", "bağımsız veriyle karşılaştırma"),
                ))
    return tuple(sonuclar)
