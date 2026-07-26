from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .olay_omurgasi import Olay


@dataclass
class RuntimeDurumu:
    aktif_katman: str = "K00"
    son_olay_kodu: str | None = None
    son_olay_turu: str | None = None
    durum: str = "BASLANGIC"
    guncelleme_zamani: str | None = None

    def guncelle(self, olay: Olay) -> None:
        self.aktif_katman = olay.hedef.value
        self.son_olay_kodu = olay.ozet_kodu
        self.son_olay_turu = olay.tur.name
        self.durum = "OLAY_ALINDI"
        self.guncelleme_zamani = datetime.now(timezone.utc).isoformat()

    def gorunum(self) -> dict[str, Any]:
        return {
            "aktif_katman": self.aktif_katman,
            "son_olay_kodu": self.son_olay_kodu,
            "son_olay_turu": self.son_olay_turu,
            "durum": self.durum,
            "guncelleme_zamani": self.guncelleme_zamani,
        }