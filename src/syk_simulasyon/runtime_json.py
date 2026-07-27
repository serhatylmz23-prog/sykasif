from __future__ import annotations

import json

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


class RuntimeJsonSaglayicisi:
    """Runtime anlık görünümünü JSON çıktısına dönüştürür."""

    def __init__(self, gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi

    def json_uret(self) -> str:
        return json.dumps(
            self._gorunum_saglayicisi.gorunum().sozluk(),
            ensure_ascii=False,
            indent=2,
        )