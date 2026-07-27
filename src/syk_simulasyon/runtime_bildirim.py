from __future__ import annotations

from collections.abc import Callable

from .olay_omurgasi import Olay


BildirimAbonesi = Callable[[Olay], None]


class RuntimeBildirimMerkezi:
    """Runtime olaylarını abonelere iletir."""

    def __init__(self) -> None:
        self._aboneler: list[BildirimAbonesi] = []

    def abone_ekle(self, abone: BildirimAbonesi) -> None:
        if abone not in self._aboneler:
            self._aboneler.append(abone)

    def abone_sil(self, abone: BildirimAbonesi) -> None:
        if abone in self._aboneler:
            self._aboneler.remove(abone)

    def yayinla(self, olay: Olay) -> None:
        for abone in tuple(self._aboneler):
            try:
                abone(olay)
            except Exception:
                continue

    @property
    def abone_sayisi(self) -> int:
        return len(self._aboneler)