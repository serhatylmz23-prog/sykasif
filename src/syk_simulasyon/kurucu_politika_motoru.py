from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
import uuid


class PolitikaTuru(StrEnum):
    ANLIK_UYARLAMA_SINIRI = "anlik_uyarlama_siniri"
    CIHAZ_YETKISI = "cihaz_yetkisi"
    MODEL_TERFISI = "model_terfisi"
    KALICI_PARAMETRE = "kalici_parametre"
    GERI_ALMA = "geri_alma"
    GUVENLI_DURDURMA = "guvenli_durdurma"


class PolitikaDurumu(StrEnum):
    TASLAK = "taslak"
    BILGE_KAAN_INCELEMESINDE = "bilge_kaan_incelemesinde"
    KURUCU_KAAN_ONAYINDA = "kurucu_kaan_onayinda"
    ETKIN = "etkin"
    ASKIYA_ALINDI = "askiya_alindi"
    GERI_ALINDI = "geri_alindi"


@dataclass(frozen=True)
class PolitikaSiniri:
    alan: str
    en_dusuk: float | None = None
    en_yuksek: float | None = None
    izinli_degerler: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.alan.strip():
            raise ValueError("Politika alanı boş olamaz")
        if self.en_dusuk is not None and self.en_yuksek is not None and self.en_dusuk > self.en_yuksek:
            raise ValueError("En düşük sınır en yüksek sınırdan büyük olamaz")

    def izinli_mi(self, deger: float | str) -> bool:
        if isinstance(deger, str):
            return deger in self.izinli_degerler if self.izinli_degerler else False
        if self.en_dusuk is not None and deger < self.en_dusuk:
            return False
        if self.en_yuksek is not None and deger > self.en_yuksek:
            return False
        return True


@dataclass
class KurucuPolitikasi:
    ad: str
    tur: PolitikaTuru
    gerekce: str
    sinirlar: tuple[PolitikaSiniri, ...] = ()
    durum: PolitikaDurumu = PolitikaDurumu.TASLAK
    bilge_kaan_onayi: bool = False
    kurucu_kaan_onayi: bool = False
    politika_id: str = field(default_factory=lambda: f"KP-{uuid.uuid4().hex[:16].upper()}")
    surum: int = 1
    onceki_politika_id: str | None = None
    olusturma_zamani: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.ad.strip() or not self.gerekce.strip():
            raise ValueError("Politika adı ve gerekçesi boş olamaz")
        if self.surum < 1:
            raise ValueError("Politika sürümü en az 1 olmalıdır")

    def parmak_izi(self) -> str:
        veri = {
            "ad": self.ad,
            "tur": self.tur,
            "gerekce": self.gerekce,
            "sinirlar": [s.__dict__ for s in self.sinirlar],
            "surum": self.surum,
            "onceki_politika_id": self.onceki_politika_id,
        }
        return sha256(json.dumps(veri, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


class KurucuKaanPolitikaMotoru:
    """Kalıcı ve sistemsel değişiklikleri çift onayla yöneten politika motoru."""

    def __init__(self) -> None:
        self._politikalar: dict[str, KurucuPolitikasi] = {}

    def kaydet(self, politika: KurucuPolitikasi) -> KurucuPolitikasi:
        if politika.politika_id in self._politikalar:
            raise ValueError("Politika kimliği zaten kayıtlı")
        self._politikalar[politika.politika_id] = politika
        return politika

    def bilge_kaan_incelemesine_gonder(self, politika_id: str) -> KurucuPolitikasi:
        p = self._getir(politika_id)
        if p.durum != PolitikaDurumu.TASLAK:
            raise ValueError("Yalnız taslak politika incelemeye gönderilebilir")
        p.durum = PolitikaDurumu.BILGE_KAAN_INCELEMESINDE
        return p

    def bilge_kaan_onayla(self, politika_id: str) -> KurucuPolitikasi:
        p = self._getir(politika_id)
        if p.durum != PolitikaDurumu.BILGE_KAAN_INCELEMESINDE:
            raise ValueError("Politika Bilge Kaan incelemesinde değil")
        p.bilge_kaan_onayi = True
        p.durum = PolitikaDurumu.KURUCU_KAAN_ONAYINDA
        return p

    def kurucu_kaan_onayla(self, politika_id: str) -> KurucuPolitikasi:
        p = self._getir(politika_id)
        if p.durum != PolitikaDurumu.KURUCU_KAAN_ONAYINDA or not p.bilge_kaan_onayi:
            raise PermissionError("Önce Bilge Kaan teknik onayı gerekir")
        p.kurucu_kaan_onayi = True
        p.durum = PolitikaDurumu.ETKIN
        return p

    def deger_izinli_mi(self, politika_id: str, alan: str, deger: float | str) -> bool:
        p = self._getir(politika_id)
        if p.durum != PolitikaDurumu.ETKIN:
            return False
        sinir = next((s for s in p.sinirlar if s.alan == alan), None)
        return bool(sinir and sinir.izinli_mi(deger))

    def geri_al(self, politika_id: str, bilge_kaan_onayi: bool, kurucu_kaan_onayi: bool) -> KurucuPolitikasi:
        p = self._getir(politika_id)
        if not (bilge_kaan_onayi and kurucu_kaan_onayi):
            raise PermissionError("Politika geri alma için Bilge Kaan ve Kurucu Kaan onayı gerekir")
        if p.durum not in {PolitikaDurumu.ETKIN, PolitikaDurumu.ASKIYA_ALINDI}:
            raise ValueError("Yalnız etkin veya askıdaki politika geri alınabilir")
        p.durum = PolitikaDurumu.GERI_ALINDI
        return p

    def yeni_surum(self, politika_id: str, gerekce: str, sinirlar: tuple[PolitikaSiniri, ...]) -> KurucuPolitikasi:
        eski = self._getir(politika_id)
        yeni = KurucuPolitikasi(
            ad=eski.ad,
            tur=eski.tur,
            gerekce=gerekce,
            sinirlar=sinirlar,
            surum=eski.surum + 1,
            onceki_politika_id=eski.politika_id,
        )
        return self.kaydet(yeni)

    def _getir(self, politika_id: str) -> KurucuPolitikasi:
        try:
            return self._politikalar[politika_id]
        except KeyError as exc:
            raise KeyError("Politika bulunamadı") from exc
