from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from itertools import product
from typing import Iterable
import json


class OrtamKategorisi(StrEnum):
    TOPRAK = "toprak"
    KAYA = "kaya"
    SU = "su"
    HAVA = "hava"
    BITKI_ORTUSU = "bitki_ortusu"
    JEOLOJI = "jeoloji"
    GOKSEL = "goksel"
    MANYETIK = "manyetik"
    ELEKTRIKSEL = "elektriksel"
    DIGER = "diger"


@dataclass(frozen=True)
class OrtamOzelligi:
    kategori: OrtamKategorisi
    ad: str
    deger: float | str | bool
    birim: str | None
    kaynak_id: str
    guven_puani: float
    varsayim_mi: bool = False

    def __post_init__(self) -> None:
        if not self.ad.strip() or not self.kaynak_id.strip():
            raise ValueError("Ortam özelliği adı ve kaynak kimliği zorunludur")
        if not 0.0 <= self.guven_puani <= 1.0:
            raise ValueError("Güven puanı 0 ile 1 arasında olmalıdır")


@dataclass(frozen=True)
class GokselZamansalBaglam:
    zaman: str
    gunes_etkinligi: float | None = None
    iyonosfer_durumu: float | None = None
    gelgit_seviyesi_m: float | None = None
    ay_evresi: str | None = None
    mevsim: str | None = None
    kaynak_id: str | None = None

    def __post_init__(self) -> None:
        for ad in ("gunes_etkinligi", "iyonosfer_durumu"):
            deger = getattr(self, ad)
            if deger is not None and not 0.0 <= deger <= 1.0:
                raise ValueError(f"{ad} 0 ile 1 arasında olmalıdır")


@dataclass(frozen=True)
class OrtamProfili:
    profil_id: str
    konum_kodu: str
    ozellikler: tuple[OrtamOzelligi, ...]
    baglam: GokselZamansalBaglam | None = None
    olusturma_zamani: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.profil_id.strip() or not self.konum_kodu.strip():
            raise ValueError("Profil kimliği ve kodlanmış konum zorunludur")
        if not self.ozellikler:
            raise ValueError("Ortam profili en az bir özellik içermelidir")

    @property
    def guven_puani(self) -> float:
        temel = sum(o.guven_puani for o in self.ozellikler) / len(self.ozellikler)
        varsayim_cezasi = min(0.35, sum(1 for o in self.ozellikler if o.varsayim_mi) * 0.05)
        return round(max(0.0, temel - varsayim_cezasi), 4)

    def parmak_izi(self) -> str:
        veri = {
            "konum_kodu": self.konum_kodu,
            "ozellikler": [o.__dict__ for o in self.ozellikler],
            "baglam": self.baglam.__dict__ if self.baglam else None,
        }
        return sha256(json.dumps(veri, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class OrtamHafizasi:
    kayitlar: dict[str, list[OrtamProfili]] = field(default_factory=dict)

    def ekle(self, profil: OrtamProfili) -> None:
        gecmis = self.kayitlar.setdefault(profil.konum_kodu, [])
        if any(p.parmak_izi() == profil.parmak_izi() for p in gecmis):
            raise ValueError("Aynı ortam profili daha önce kaydedilmiş")
        gecmis.append(profil)

    def gecmis(self, konum_kodu: str) -> tuple[OrtamProfili, ...]:
        return tuple(self.kayitlar.get(konum_kodu, ()))

    def son_profil(self, konum_kodu: str) -> OrtamProfili | None:
        kayitlar = self.kayitlar.get(konum_kodu, [])
        return kayitlar[-1] if kayitlar else None


@dataclass(frozen=True)
class DeneyBilesimi:
    hedef_id: str
    ortam_profil_id: str
    derinlik_m: float
    frekans_hz: float
    tekrar_no: int = 1

    def __post_init__(self) -> None:
        if not 0.0 < self.derinlik_m <= 2.25:
            raise ValueError("Derinlik 0 ile 2,25 metre arasında olmalıdır")
        if self.frekans_hz <= 0:
            raise ValueError("Frekans pozitif olmalıdır")
        if self.tekrar_no < 1:
            raise ValueError("Tekrar numarası en az 1 olmalıdır")

    def parmak_izi(self, derinlik_hassasiyeti_m: float = 0.02, frekans_hassasiyeti_hz: float = 1.0) -> str:
        if derinlik_hassasiyeti_m <= 0 or frekans_hassasiyeti_hz <= 0:
            raise ValueError("Hassasiyet değerleri pozitif olmalıdır")
        d = round(self.derinlik_m / derinlik_hassasiyeti_m)
        f = round(self.frekans_hz / frekans_hassasiyeti_hz)
        veri = f"{self.hedef_id}|{self.ortam_profil_id}|{d}|{f}"
        return sha256(veri.encode()).hexdigest()


@dataclass
class KontrolluDeneyBilesimUreticisi:
    en_fazla_senaryo: int = 10_000
    uretilen_parmak_izleri: set[str] = field(default_factory=set)

    def uret(
        self,
        hedef_ids: Iterable[str],
        ortam_profil_ids: Iterable[str],
        derinlikler_m: Iterable[float],
        frekanslar_hz: Iterable[float],
    ) -> list[DeneyBilesimi]:
        hedefler = tuple(hedef_ids)
        ortamlar = tuple(ortam_profil_ids)
        derinlikler = tuple(float(v) for v in derinlikler_m)
        frekanslar = tuple(float(v) for v in frekanslar_hz)
        adet = len(hedefler) * len(ortamlar) * len(derinlikler) * len(frekanslar)
        if adet > self.en_fazla_senaryo:
            raise OverflowError(f"Deney bileşimi sınırı aşıldı: {adet} > {self.en_fazla_senaryo}")
        sonuc: list[DeneyBilesimi] = []
        for h, o, d, f in product(hedefler, ortamlar, derinlikler, frekanslar):
            deney = DeneyBilesimi(h, o, d, f)
            iz = deney.parmak_izi()
            if iz in self.uretilen_parmak_izleri:
                continue
            self.uretilen_parmak_izleri.add(iz)
            sonuc.append(deney)
        return sonuc
