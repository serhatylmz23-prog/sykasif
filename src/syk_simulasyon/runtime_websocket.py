from __future__ import annotations
from dataclasses import asdict, is_dataclass

from typing import Any


class RuntimeWebSocketYayincisi:
    """
    Runtime verisini WebSocket istemcilerine hazırlayan katman.
    """

    def __init__(
        self,
        gorunum_saglayici: Any,
        sistem_hazirlik_saglayici: Any | None = None,
    ) -> None:
        self._gorunum_saglayici = gorunum_saglayici
        self._sistem_hazirlik_saglayici = (
            sistem_hazirlik_saglayici
        )

    def baglanti_mesaji(self) -> dict[str, Any]:
        return {
            "mesaj": "SyOtağı bağlantısı kuruldu",
            "terminal": "SYK-FIELD-01",
            "gorunum": self._gorunum(),
            "sistem_hazirlik": self._sistem_hazirlik(),
        }

    def guncelleme_mesaji(self) -> dict[str, Any]:
        return {
            "mesaj": "Canlı görünüm güncellendi",
            "terminal": "SYK-FIELD-01",
            "gorunum": self._gorunum(),
            "sistem_hazirlik": self._sistem_hazirlik(),
        }

    def bilinmeyen_komut(self, komut: str) -> dict[str, Any]:
        return {
            "mesaj": "Bilinmeyen komut",
            "komut": komut,
        }

    def _sistem_hazirlik(self) -> dict[str, Any]:
        saglayici = self._sistem_hazirlik_saglayici

        if saglayici is None:
            return {}

        if callable(saglayici):
            sonuc = saglayici()
        elif hasattr(saglayici, "sistem_hazirlik_ozeti"):
            sonuc = saglayici.sistem_hazirlik_ozeti()
        else:
            raise TypeError(
                "Sistem hazırlık sağlayıcısı çağrılabilir "
                "olmalı veya sistem_hazirlik_ozeti "
                "yöntemini sunmalıdır."
            )

        if not isinstance(sonuc, dict):
            raise TypeError(
                "Sistem hazırlık sağlayıcısı sözlük "
                "üretmelidir."
            )

        return dict(sonuc)

    def _gorunum(self) -> dict[str, Any]:
        saglayici = self._gorunum_saglayici

        if hasattr(saglayici, "olustur"):
            gorunum = saglayici.olustur()
        elif hasattr(saglayici, "gorunum"):
            gorunum = saglayici.gorunum()
        else:
            return {
                "durum": "hazır",
                "aktif_modul": "runtime",
                "ilerleme_yuzdesi": 0,
                "olay_sayisi": 0,
            }

        if isinstance(gorunum, dict):
            return dict(gorunum)

        if is_dataclass(gorunum) and not isinstance(
            gorunum,
            type,
        ):
            return asdict(gorunum)

        if hasattr(gorunum, "model_dump"):
            sonuc = gorunum.model_dump()

            if isinstance(sonuc, dict):
                return sonuc

        if hasattr(gorunum, "to_dict"):
            sonuc = gorunum.to_dict()

            if isinstance(sonuc, dict):
                return sonuc

        raise TypeError(
            "Runtime görünüm sağlayıcısı sözlük veya "
            "sözlüğe dönüştürülebilir bir görünüm üretmelidir."
        )
