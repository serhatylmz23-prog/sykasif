from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from .olay_omurgasi import Olay, OlayTuru
from .ortak_dil import Katman


class RuntimeDurumTuru(StrEnum):
    BASLATILIYOR = "başlatılıyor"
    HAZIR = "hazır"
    CALISIYOR = "çalışıyor"
    BEKLEMEDE = "beklemede"
    UYKU = "uyku"
    ONAY_BEKLIYOR = "onay_bekliyor"
    TAMAMLANDI = "tamamlandı"
    HATA = "hata"
    GUVENLI_DURDURULDU = "güvenli_durduruldu"


@dataclass
class RuntimeDurumu:
    durum: RuntimeDurumTuru = RuntimeDurumTuru.BASLATILIYOR
    aktif_katman: Katman | None = None
    aktif_modul: str | None = None
    ilerleme_yuzdesi: float = 0.0
    son_olay_kimligi: str | None = None
    son_olay_kodu: str | None = None
    son_olay_turu: OlayTuru | None = None
    guncelleme_zamani: str | None = None

    def durum_guncelle(
        self,
        *,
        durum: RuntimeDurumTuru,
        aktif_modul: str | None = None,
        ilerleme_yuzdesi: float | None = None,
    ) -> None:
        if ilerleme_yuzdesi is not None:
            if not 0.0 <= ilerleme_yuzdesi <= 100.0:
                raise ValueError(
                    "İlerleme yüzdesi 0 ile 100 arasında olmalıdır"
                )
            self.ilerleme_yuzdesi = ilerleme_yuzdesi

        if durum == RuntimeDurumTuru.TAMAMLANDI:
            if self.ilerleme_yuzdesi != 100.0:
                raise ValueError(
                    "İlerleme yüzde 100 olmadan durum tamamlandı yapılamaz"
                )

        self.durum = durum

        if aktif_modul is not None:
            temiz_modul = aktif_modul.strip()
            if not temiz_modul:
                raise ValueError("Aktif modül adı boş olamaz")
            self.aktif_modul = temiz_modul

        self.guncelleme_zamani = datetime.now(timezone.utc).isoformat()

    def olaydan_guncelle(self, olay: Olay) -> None:
        self.aktif_katman = olay.hedef
        self.son_olay_kimligi = olay.olay_kimligi
        self.son_olay_kodu = olay.ozet_kodu
        self.son_olay_turu = olay.tur

        if olay.tur == OlayTuru.KANIT:
            self.durum = RuntimeDurumTuru.ONAY_BEKLIYOR
        elif olay.tur == OlayTuru.ACIL_DURDUR:
            self.durum = RuntimeDurumTuru.GUVENLI_DURDURULDU
        elif olay.tur == OlayTuru.GOREV_SONUCU:
            self.durum = RuntimeDurumTuru.BEKLEMEDE
        else:
            self.durum = RuntimeDurumTuru.CALISIYOR

        self.guncelleme_zamani = datetime.now(timezone.utc).isoformat()

    def gorunum(self) -> dict[str, Any]:
        return {
            "durum": self.durum.value,
            "aktif_katman": (
                self.aktif_katman.value
                if self.aktif_katman is not None
                else None
            ),
            "aktif_modul": self.aktif_modul,
            "ilerleme_yuzdesi": self.ilerleme_yuzdesi,
            "son_olay_kimligi": self.son_olay_kimligi,
            "son_olay_kodu": self.son_olay_kodu,
            "son_olay_turu": (
                self.son_olay_turu.value
                if self.son_olay_turu is not None
                else None
            ),
            "guncelleme_zamani": self.guncelleme_zamani,
        }