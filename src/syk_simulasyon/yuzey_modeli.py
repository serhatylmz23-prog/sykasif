from __future__ import annotations

from dataclasses import dataclass

from .yansima_turleri import YansimaTuru


@dataclass(frozen=True, slots=True)
class YuzeyModeli:
    yuzey_kimligi: str
    puruzluluk_0_1: float
    yonelim_derece: float = 0.0
    yansima_turu: YansimaTuru = YansimaTuru.KARMA
    malzeme_kimligi: str | None = None
    geometri_kimligi: str | None = None

    def dogrula(self) -> None:
        if not self.yuzey_kimligi.strip():
            raise ValueError("yuzey_kimligi boş olamaz")
        if not 0.0 <= self.puruzluluk_0_1 <= 1.0:
            raise ValueError("puruzluluk_0_1 0 ile 1 arasında olmalıdır")
        if not -90.0 <= self.yonelim_derece <= 90.0:
            raise ValueError("yonelim_derece -90 ile 90 arasında olmalıdır")
