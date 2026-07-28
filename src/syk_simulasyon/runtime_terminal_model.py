from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyOtagiDurumu:
    runtime_durumu: str
    websocket_durumu: str
    sistem_durumu: str
    baslangic: str
    hedef: str
    rota: str

    def sozluk(self) -> dict[str, str]:
        return {
            "runtime_durumu": self.runtime_durumu,
            "websocket_durumu": self.websocket_durumu,
            "sistem_durumu": self.sistem_durumu,
            "baslangic": self.baslangic,
            "hedef": self.hedef,
            "rota": self.rota,
        }