from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


@dataclass(frozen=True)
class RuntimeRaporu:
    baslik: str
    durum: str
    aktif_modul: str | None
    ilerleme_yuzdesi: float
    olay_sayisi: int
    guncelleme_zamani: str | None

    def sozluk(self) -> dict[str, Any]:
        return {
            "baslik": self.baslik,
            "durum": self.durum,
            "aktif_modul": self.aktif_modul,
            "ilerleme_yuzdesi": self.ilerleme_yuzdesi,
            "olay_sayisi": self.olay_sayisi,
            "guncelleme_zamani": self.guncelleme_zamani,
        }


class RuntimeRaporlayici:
    """Runtime anlık görünümünden sade bir durum raporu üretir."""

    def __init__(
        self,
        gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi,
    ) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi

    def rapor_uret(self, baslik: str = "SyKaşif Runtime Raporu") -> RuntimeRaporu:
        gorunum = self._gorunum_saglayicisi.gorunum()

        return RuntimeRaporu(
            baslik=baslik,
            durum=gorunum.durum,
            aktif_modul=gorunum.aktif_modul,
            ilerleme_yuzdesi=gorunum.ilerleme_yuzdesi,
            olay_sayisi=gorunum.olay_sayisi,
            guncelleme_zamani=gorunum.guncelleme_zamani,
        )