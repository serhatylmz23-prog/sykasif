from __future__ import annotations

import csv
import io

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


class RuntimeCsvSaglayicisi:
    """Runtime anlık görünümünü CSV çıktısına dönüştürür."""

    def __init__(
        self,
        gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi,
    ) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi

    def csv_uret(self) -> str:
        gorunum = self._gorunum_saglayicisi.gorunum().sozluk()

        cikti = io.StringIO()
        yazici = csv.DictWriter(
            cikti,
            fieldnames=list(gorunum.keys()),
        )

        yazici.writeheader()
        yazici.writerow(gorunum)

        return cikti.getvalue()