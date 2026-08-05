"""UGR Runtime 8013 canlı olay modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class UgrCanliOlayTuru(StrEnum):
    """Runtime 8013 üzerinden taşınan olay türleri."""

    MANIFEST_YUKLENDI = "manifest_yuklendi"
    IKON_DURUMU = "ikon_durumu"
    IKON_GORUNUMU = "ikon_gorunumu"
    IKON_AKTIFLIGI = "ikon_aktifligi"
    TOPLU_GUNCELLEME = "toplu_guncelleme"
    SNAPSHOT = "snapshot"
    BAGLANTI = "baglanti"
    KALP_ATISI = "kalp_atisi"
    HATA = "hata"


def utc_simdi() -> datetime:
    """UTC zaman damgası üretir."""

    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class UgrCanliIkonOlayi:
    """Runtime 8013 canlı ikon olay taşıyıcısı."""

    olay_turu: UgrCanliOlayTuru
    veri: dict[str, Any]
    ikon_kimligi: str | None = None
    olay_kimligi: str = field(
        default_factory=lambda: uuid4().hex
    )
    zaman: datetime = field(
        default_factory=utc_simdi
    )

    def __post_init__(self) -> None:
        if not self.olay_kimligi.strip():
            raise ValueError(
                "olay_kimligi boş olamaz."
            )

        if self.ikon_kimligi is not None:
            if not self.ikon_kimligi.strip():
                raise ValueError(
                    "ikon_kimligi boş olamaz."
                )

    def json_verisi(self) -> dict[str, Any]:
        """JSON uyumlu olay sözlüğü üretir."""

        return {
            "olay_kimligi": self.olay_kimligi,
            "olay_turu": self.olay_turu.value,
            "ikon_kimligi": self.ikon_kimligi,
            "zaman": self.zaman.isoformat(),
            "veri": dict(self.veri),
        }
