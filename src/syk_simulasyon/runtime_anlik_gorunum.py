from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .runtime_izleme import RuntimeIzlemeSaglayicisi


@dataclass(frozen=True)
class RuntimeAnlikGorunum:
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


class RuntimeAnlikGorunumSaglayicisi:
    """Runtime izleme verisini arayüz sözleşmesine dönüştürür."""

    def __init__(self, izleme: RuntimeIzlemeSaglayicisi) -> None:
        self._izleme = izleme

    def gorunum(self) -> RuntimeAnlikGorunum:
        kaynak = self._izleme.gorunum()

        return RuntimeAnlikGorunum(
            durum=kaynak.durum,
            aktif_katman=kaynak.aktif_katman,
            aktif_modul=kaynak.aktif_modul,
            ilerleme_yuzdesi=kaynak.ilerleme_yuzdesi,
            son_olay_kimligi=kaynak.son_olay_kimligi,
            son_olay_kodu=kaynak.son_olay_kodu,
            son_olay_turu=kaynak.son_olay_turu,
            guncelleme_zamani=kaynak.guncelleme_zamani,
            olay_sayisi=kaynak.olay_sayisi,
        )