from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import json


class HedefAilesi(StrEnum):
    MALZEME = "malzeme"
    MINERAL = "mineral"
    KAYA = "kaya"
    BOSLUK = "bosluk"
    GEOMETRIK_YAPI = "geometrik_yapi"
    TARIHSEL_YAPI = "tarihsel_yapi"
    ANOMALI = "anomali"


class KaynakNiteligi(StrEnum):
    BIRINCIL_BILIMSEL = "birincil_bilimsel"
    RESMI_TEKNIK = "resmi_teknik"
    IKINCIL_BILIMSEL = "ikincil_bilimsel"
    UZMAN_GORUSU = "uzman_gorusu"
    SIMULASYON_VARSAYIMI = "simulasyon_varsayimi"
    DOGRULANMAMIS = "dogrulanmamis"


KAYNAK_TABAN_PUANI = {
    KaynakNiteligi.BIRINCIL_BILIMSEL: 0.95,
    KaynakNiteligi.RESMI_TEKNIK: 0.90,
    KaynakNiteligi.IKINCIL_BILIMSEL: 0.78,
    KaynakNiteligi.UZMAN_GORUSU: 0.65,
    KaynakNiteligi.SIMULASYON_VARSAYIMI: 0.40,
    KaynakNiteligi.DOGRULANMAMIS: 0.10,
}


@dataclass(frozen=True)
class BilimselKaynak:
    kaynak_id: str
    nitelik: KaynakNiteligi
    baslik: str
    yayin_yili: int | None = None
    doi_veya_belge_no: str | None = None
    erisim_adresi: str | None = None
    dogrudan_desteklenen_alanlar: tuple[str, ...] = ()
    belirsizlik_notu: str | None = None

    def __post_init__(self) -> None:
        if not self.kaynak_id.strip() or not self.baslik.strip():
            raise ValueError("Kaynak kimliği ve başlığı zorunludur")
        if self.nitelik in {KaynakNiteligi.BIRINCIL_BILIMSEL, KaynakNiteligi.RESMI_TEKNIK} and not (
            self.doi_veya_belge_no or self.erisim_adresi
        ):
            raise ValueError("Güçlü kaynak için DOI, belge numarası veya erişim adresi gereklidir")

    @property
    def guven_puani(self) -> float:
        puan = KAYNAK_TABAN_PUANI[self.nitelik]
        if self.belirsizlik_notu:
            puan -= 0.08
        if not self.dogrudan_desteklenen_alanlar:
            puan -= 0.10
        return round(max(0.0, min(1.0, puan)), 4)


@dataclass(frozen=True)
class FizikselOzellik:
    ad: str
    deger: float | str | bool
    birim: str | None
    kaynak_id: str
    varsayim_mi: bool = False

    def __post_init__(self) -> None:
        if not self.ad.strip() or not self.kaynak_id.strip():
            raise ValueError("Özellik adı ve kaynak kimliği zorunludur")


@dataclass
class HedefAltSinifi:
    hedef_id: str
    aile: HedefAilesi
    ad: str
    ust_hedef_id: str | None = None
    aciklama: str = ""
    ozellikler: list[FizikselOzellik] = field(default_factory=list)
    izinli_geometriler: tuple[str, ...] = ()
    bilinmeyen_alanlar: tuple[str, ...] = ()
    etiketler: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.hedef_id.strip() or not self.ad.strip():
            raise ValueError("Hedef kimliği ve adı zorunludur")
        if self.aile in {HedefAilesi.MALZEME, HedefAilesi.MINERAL, HedefAilesi.KAYA} and not self.ozellikler:
            raise ValueError("Malzeme, mineral ve kaya alt sınıfları en az bir fiziksel özellik içermelidir")

    def kaynak_kimlikleri(self) -> set[str]:
        return {o.kaynak_id for o in self.ozellikler}

    def icerik_sha256(self) -> str:
        veri = {
            "hedef_id": self.hedef_id,
            "aile": self.aile,
            "ad": self.ad,
            "ust_hedef_id": self.ust_hedef_id,
            "aciklama": self.aciklama,
            "ozellikler": [o.__dict__ for o in self.ozellikler],
            "izinli_geometriler": self.izinli_geometriler,
            "bilinmeyen_alanlar": self.bilinmeyen_alanlar,
            "etiketler": self.etiketler,
        }
        return sha256(json.dumps(veri, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class HedefSicili:
    kaynaklar: dict[str, BilimselKaynak] = field(default_factory=dict)
    hedefler: dict[str, HedefAltSinifi] = field(default_factory=dict)

    def kaynak_ekle(self, kaynak: BilimselKaynak) -> None:
        if kaynak.kaynak_id in self.kaynaklar:
            raise ValueError("Kaynak kimliği zaten kayıtlı")
        self.kaynaklar[kaynak.kaynak_id] = kaynak

    def hedef_ekle(self, hedef: HedefAltSinifi) -> None:
        if hedef.hedef_id in self.hedefler:
            raise ValueError("Hedef kimliği zaten kayıtlı")
        eksik = hedef.kaynak_kimlikleri() - self.kaynaklar.keys()
        if eksik:
            raise ValueError(f"Eksik kaynak kayıtları: {sorted(eksik)}")
        if hedef.ust_hedef_id and hedef.ust_hedef_id not in self.hedefler:
            raise ValueError("Üst hedef önce kaydedilmelidir")
        self.hedefler[hedef.hedef_id] = hedef

    def aileye_gore(self, aile: HedefAilesi) -> tuple[HedefAltSinifi, ...]:
        return tuple(h for h in self.hedefler.values() if h.aile == aile)

    def hedef_guven_puani(self, hedef_id: str) -> float:
        hedef = self.hedefler[hedef_id]
        kaynaklar = [self.kaynaklar[k] for k in hedef.kaynak_kimlikleri()]
        if not kaynaklar:
            return 0.0
        taban = sum(k.guven_puani for k in kaynaklar) / len(kaynaklar)
        varsayim_orani = sum(1 for o in hedef.ozellikler if o.varsayim_mi) / len(hedef.ozellikler)
        bilinmeyen_cezasi = min(0.30, len(hedef.bilinmeyen_alanlar) * 0.05)
        return round(max(0.0, taban - varsayim_orani * 0.25 - bilinmeyen_cezasi), 4)
