from __future__ import annotations

from collections.abc import Callable

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


CanliAbone = Callable[[dict[str, object]], None]


class RuntimeCanliGecit:
    """Runtime görünümünü canlı abonelere iletir."""

    def __init__(
        self,
        gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi,
    ) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi
        self._aboneler: list[CanliAbone] = []

    def abone_ekle(self, abone: CanliAbone) -> None:
        if abone not in self._aboneler:
            self._aboneler.append(abone)

    def abone_sil(self, abone: CanliAbone) -> None:
        if abone in self._aboneler:
            self._aboneler.remove(abone)

    def yayinla(self) -> dict[str, object]:
        gorunum = self._gorunum_saglayicisi.gorunum().sozluk()

        for abone in tuple(self._aboneler):
            try:
                abone(gorunum)
            except Exception:
                continue

        return gorunum

    @property
    def abone_sayisi(self) -> int:
        return len(self._aboneler)