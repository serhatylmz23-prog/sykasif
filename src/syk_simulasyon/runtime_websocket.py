from __future__ import annotations

from typing import Any


class RuntimeWebSocketYayincisi:
    """
    Runtime verisini WebSocket istemcilerine hazırlayan katman.
    """

    def __init__(self, gorunum_saglayici: Any) -> None:
        self._gorunum_saglayici = gorunum_saglayici

    def baglanti_mesaji(self) -> dict[str, Any]:
        return {
            "mesaj": "SyOtağı bağlantısı kuruldu",
            "terminal": "SYK-FIELD-01",
            "gorunum": self._gorunum(),
        }

    def guncelleme_mesaji(self) -> dict[str, Any]:
        return {
            "mesaj": "Canlı görünüm güncellendi",
            "terminal": "SYK-FIELD-01",
            "gorunum": self._gorunum(),
        }

    def bilinmeyen_komut(self, komut: str) -> dict[str, Any]:
        return {
            "mesaj": "Bilinmeyen komut",
            "komut": komut,
        }

    def _gorunum(self) -> dict[str, Any]:
        if hasattr(self._gorunum_saglayici, "olustur"):
            return self._gorunum_saglayici.olustur()

        return {
            "durum": "hazır",
            "aktif_modul": "runtime",
            "ilerleme_yuzdesi": 0,
            "olay_sayisi": 0,
        }