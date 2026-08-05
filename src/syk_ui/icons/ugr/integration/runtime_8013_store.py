"""UGR Runtime 8013 thread-safe olay deposu."""

from __future__ import annotations

from collections import deque
from threading import Condition, RLock
from time import monotonic
from typing import Final

from .runtime_8013_events import (
    UgrCanliIkonOlayi,
)


class UgrRuntime8013EventStore:
    """Canlı ikon olaylarını sınırlı bellekte tutar."""

    VARSAYILAN_KAPASITE: Final[int] = 2048

    def __init__(
        self,
        *,
        kapasite: int = VARSAYILAN_KAPASITE,
    ) -> None:
        if kapasite <= 0:
            raise ValueError(
                "kapasite sıfırdan büyük olmalıdır."
            )

        self._olaylar: deque[
            UgrCanliIkonOlayi
        ] = deque(
            maxlen=kapasite
        )

        self._kilit = RLock()
        self._kosul = Condition(
            self._kilit
        )
        self._sira = 0

    @property
    def kapasite(self) -> int:
        """Olay deposu kapasitesini döndürür."""

        return int(
            self._olaylar.maxlen or 0
        )

    def ekle(
        self,
        olay: UgrCanliIkonOlayi,
    ) -> int:
        """Olay ekler ve sıra numarasını döndürür."""

        with self._kosul:
            self._sira += 1
            self._olaylar.append(olay)
            self._kosul.notify_all()

            return self._sira

    def tumu(
        self,
    ) -> tuple[UgrCanliIkonOlayi, ...]:
        """Depodaki bütün olayları döndürür."""

        with self._kilit:
            return tuple(
                self._olaylar
            )

    def son(
        self,
        adet: int = 1,
    ) -> tuple[UgrCanliIkonOlayi, ...]:
        """Son olayları döndürür."""

        if adet < 0:
            raise ValueError(
                "adet negatif olamaz."
            )

        with self._kilit:
            if adet == 0:
                return ()

            return tuple(
                list(self._olaylar)[-adet:]
            )

    def bekle(
        self,
        *,
        onceki_sira: int,
        zaman_asimi: float = 15.0,
    ) -> tuple[
        int,
        tuple[UgrCanliIkonOlayi, ...],
    ]:
        """Yeni olay oluşana kadar bekler."""

        if onceki_sira < 0:
            raise ValueError(
                "onceki_sira negatif olamaz."
            )

        if zaman_asimi < 0:
            raise ValueError(
                "zaman_asimi negatif olamaz."
            )

        baslangic = monotonic()

        with self._kosul:
            while self._sira <= onceki_sira:
                kalan = (
                    zaman_asimi
                    - (
                        monotonic()
                        - baslangic
                    )
                )

                if kalan <= 0:
                    return self._sira, ()

                self._kosul.wait(
                    timeout=kalan
                )

            yeni_sira = self._sira

            fark = max(
                1,
                yeni_sira - onceki_sira,
            )

            olaylar = tuple(
                list(self._olaylar)[-fark:]
            )

            return yeni_sira, olaylar

    def temizle(self) -> None:
        """Olay deposunu temizler."""

        with self._kosul:
            self._olaylar.clear()
            self._kosul.notify_all()

    def durum_ozeti(self) -> dict[str, int]:
        """Olay deposu özetini döndürür."""

        with self._kilit:
            return {
                "olay_sayisi": len(
                    self._olaylar
                ),
                "kapasite": self.kapasite,
                "son_sira": self._sira,
            }
