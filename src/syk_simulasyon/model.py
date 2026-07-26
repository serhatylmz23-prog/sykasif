from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any
import json
import uuid

class VeriKaynagi(StrEnum):
    SIMULASYON = "simulasyon"
    GERCEK_SENSOR = "gercek_sensor"
    KAMERA = "kamera"
    GPS = "gps"
    HARITA = "harita"
    LITERATUR = "literatur"
    KULLANICI = "kullanici"

class BilinmezlikNedeni(StrEnum):
    BILINMIYOR = "bilinmiyor"
    VERI_YETERSIZ = "veri_yetersiz"
    OLCUM_YOK = "olcum_yok"
    EKSIK_DOSYA = "eksik_dosya"
    HENUZ_DESTEKLENMIYOR = "henuz_desteklenmiyor"
    UZMAN_INCELEMESI_GEREKLI = "uzman_incelemesi_gerekli"

class KanitSeviyesi(StrEnum):
    VARSAYIM = "varsayim"
    SIMULASYON = "simulasyon"
    TEKRARLANMIS_SIMULASYON = "tekrarlanmis_simulasyon"
    SAHA_ADAYI = "saha_adayi"
    SAHA_DOGRULANMIS = "saha_dogrulanmis"
    BAGIMSIZ_DOGRULANMIS = "bagimsiz_dogrulanmis"

@dataclass(frozen=True)
class KaynakReferansi:
    tur: VeriKaynagi
    kimlik: str
    surum: str | None = None
    sha256: str | None = None
    guven_puani: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.guven_puani <= 1.0:
            raise ValueError("Güven puanı 0 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class Varsayim:
    alan: str
    deger: Any
    gerekce: str
    guven_puani: float

@dataclass(frozen=True)
class Celiski:
    konu: str
    birinci_iddia: str
    ikinci_iddia: str
    etkisi: str
    ek_veri_ihtiyaci: tuple[str, ...] = ()

@dataclass(frozen=True)
class ArastirmaOnerisi:
    baslik: str
    gerekce: str
    bilgi_kazanci: float
    maliyet_puani: float
    risk_puani: float

    @property
    def oncelik_puani(self) -> float:
        # Bilgi kazancı yükseltir; maliyet ve risk düşürür.
        return round(max(0.0, min(1.0, self.bilgi_kazanci * 0.65 + (1-self.maliyet_puani)*0.2 + (1-self.risk_puani)*0.15)), 4)

@dataclass
class SimulasyonKaydi:
    hedef_sinifi: str
    derinlik_m: float
    kaynaklar: list[KaynakReferansi]
    ortam: dict[str, Any]
    sensor: dict[str, Any]
    varsayimlar: list[Varsayim] = field(default_factory=list)
    celiskiler: list[Celiski] = field(default_factory=list)
    bilinmezlikler: list[BilinmezlikNedeni] = field(default_factory=list)
    arastirma_onerileri: list[ArastirmaOnerisi] = field(default_factory=list)
    kanit_seviyesi: KanitSeviyesi = KanitSeviyesi.VARSAYIM
    kayit_id: str = field(default_factory=lambda: f"SVM-{uuid.uuid4().hex[:16].upper()}")
    olusturma_zamani: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not 0 < self.derinlik_m <= 2.25:
            raise ValueError("İlk aşama derinliği 0'dan büyük ve en fazla 2,25 metre olmalıdır")
        if not self.hedef_sinifi.strip():
            raise ValueError("Hedef sınıfı boş olamaz")
        if not self.kaynaklar:
            self.bilinmezlikler.append(BilinmezlikNedeni.VERI_YETERSIZ)

    def guven_puani(self) -> float:
        kaynak = sum(k.guven_puani for k in self.kaynaklar) / len(self.kaynaklar) if self.kaynaklar else 0.0
        ceza = min(0.65, len(self.celiskiler)*0.12 + len(self.bilinmezlikler)*0.10)
        return round(max(0.0, min(1.0, kaynak - ceza)), 4)

    def kanit_ozeti(self) -> dict[str, Any]:
        if self.bilinmezlikler:
            ifade = "Veri yetersiz veya bilinmeyen alanlar vardır."
        elif self.celiskiler:
            ifade = "Çelişkiler çözülmeden kesin değerlendirme yapılamaz."
        else:
            ifade = "Mevcut kanıtlar simülasyon düzeyinde tutarlıdır."
        return {"kayit_id": self.kayit_id, "guven_puani": self.guven_puani(), "kanit_seviyesi": self.kanit_seviyesi, "ifade": ifade}

    def icerik_ozeti_sha256(self) -> str:
        veri = {
            "hedef_sinifi": self.hedef_sinifi,
            "derinlik_m": self.derinlik_m,
            "ortam": self.ortam,
            "sensor": self.sensor,
            "kaynaklar": [k.__dict__ for k in self.kaynaklar],
        }
        return sha256(json.dumps(veri, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()
