from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .runtime_servisi import RuntimeServisi


@dataclass(frozen=True)
class RuntimeIzlemeGorunumu:
    durum: str
    aktif_katman: str | None
    aktif_modul: str | None
    ilerleme_yuzdesi: float
    son_olay_kimligi: str | None
    son_olay_kodu: str | None
    son_olay_turu: str | None
    guncelleme_zamani: str | None
    olay_sayisi: int

    def sozluk(self) -> dict[str, Any]:
        return {
            "durum": self.durum,
            "aktif_katman": self.aktif_katman,
            "aktif_modul": self.aktif_modul,
            "ilerleme_yuzdesi": self.ilerleme_yuzdesi,
            "son_olay_kimligi": self.son_olay_kimligi,
            "son_olay_kodu": self.son_olay_kodu,
            "son_olay_turu": self.son_olay_turu,
            "guncelleme_zamani": self.guncelleme_zamani,
            "olay_sayisi": self.olay_sayisi,
        }


class RuntimeIzlemeSaglayicisi:
    """Runtime bilgisini arayüzlerden bağımsız, salt okunur biçimde sunar."""

    def __init__(self, servis: RuntimeServisi) -> None:
        self._servis = servis

    def gorunum(self) -> RuntimeIzlemeGorunumu:
        runtime = self._servis.gorunum()

        return RuntimeIzlemeGorunumu(
            durum=str(runtime["durum"]),
            aktif_katman=runtime["aktif_katman"],
            aktif_modul=runtime["aktif_modul"],
            ilerleme_yuzdesi=float(runtime["ilerleme_yuzdesi"]),
            son_olay_kimligi=runtime["son_olay_kimligi"],
            son_olay_kodu=runtime["son_olay_kodu"],
            son_olay_turu=runtime["son_olay_turu"],
            guncelleme_zamani=runtime["guncelleme_zamani"],
            olay_sayisi=len(self._servis.olay_gecmisi()),
        )