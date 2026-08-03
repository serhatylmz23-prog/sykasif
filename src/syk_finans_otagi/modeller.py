from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class VarlikTuru(StrEnum):
    HISSE = "hisse"
    FON = "fon"
    ALTIN = "altin"
    GUMUS = "gumus"
    DOVIZ = "doviz"
    DIGER = "diger"


class YatirimKosulu(StrEnum):
    SERBEST = "serbest"
    KENDI_SECIMI = "kendi_secimi"
    KASIF_ONERISI = "kasif_onerisi"


class VeriAkisDurumu(StrEnum):
    ANLIK = "anlik"
    GECIKMELI = "gecikmeli"
    CEVRIMDISI = "cevrimdisi"


@dataclass(frozen=True, slots=True)
class VeriGuncelligi:
    durum: VeriAkisDurumu
    kaynak: str
    son_guncelleme: str
    gecikme_saniyesi: int = 0
    internet_var: bool = True

    @classmethod
    def anlik(
        cls,
        *,
        kaynak: str,
        son_guncelleme: str | None = None,
    ) -> "VeriGuncelligi":
        return cls(
            durum=VeriAkisDurumu.ANLIK,
            kaynak=kaynak,
            son_guncelleme=(
                son_guncelleme
                or datetime.now(UTC).isoformat()
            ),
            gecikme_saniyesi=0,
            internet_var=True,
        )

    @classmethod
    def gecikmeli(
        cls,
        *,
        kaynak: str,
        gecikme_saniyesi: int,
        son_guncelleme: str | None = None,
    ) -> "VeriGuncelligi":
        if gecikme_saniyesi <= 0:
            raise ValueError(
                "Gecikme süresi pozitif olmalıdır."
            )

        return cls(
            durum=VeriAkisDurumu.GECIKMELI,
            kaynak=kaynak,
            son_guncelleme=(
                son_guncelleme
                or datetime.now(UTC).isoformat()
            ),
            gecikme_saniyesi=gecikme_saniyesi,
            internet_var=True,
        )

    @classmethod
    def cevrimdisi(
        cls,
        *,
        kaynak: str,
        son_guncelleme: str,
        gecikme_saniyesi: int,
    ) -> "VeriGuncelligi":
        return cls(
            durum=VeriAkisDurumu.CEVRIMDISI,
            kaynak=kaynak,
            son_guncelleme=son_guncelleme,
            gecikme_saniyesi=max(
                0,
                int(gecikme_saniyesi),
            ),
            internet_var=False,
        )

    @property
    def aciklama(self) -> str:
        if self.durum == VeriAkisDurumu.ANLIK:
            return (
                "Veri durumu: Anlık · "
                f"Kaynak: {self.kaynak} · "
                f"Son güncelleme: {self.son_guncelleme}"
            )

        if self.durum == VeriAkisDurumu.GECIKMELI:
            dakika = self.gecikme_saniyesi / 60

            return (
                "Veri durumu: Gecikmeli · "
                f"Yaklaşık gecikme: {dakika:.1f} dakika · "
                f"Kaynak: {self.kaynak} · "
                f"Son güncelleme: {self.son_guncelleme}"
            )

        dakika = self.gecikme_saniyesi / 60

        return (
            "Çevrimdışı görünüm · "
            f"Son alınan veri yaklaşık {dakika:.1f} dakika önce · "
            "Bağlantı geldiğinde yenilenecek · "
            f"Kaynak: {self.kaynak}"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "durum": self.durum.value,
            "kaynak": self.kaynak,
            "son_guncelleme": self.son_guncelleme,
            "gecikme_saniyesi": self.gecikme_saniyesi,
            "internet_var": self.internet_var,
            "aciklama": self.aciklama,
        }