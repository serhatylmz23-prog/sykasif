"""UGR dinamik ikon veri modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .durumlar import (
    IkonAnimasyonTuru,
    IkonCalismaDurumu,
    IkonGorunumModu,
    IkonOnceligi,
    IkonRenkRolu,
)


def simdi() -> datetime:
    """UTC zaman damgası üretir."""

    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class IkonDurumStili:
    """Bir çalışma durumunun görsel karşılığı."""

    durum: IkonCalismaDurumu
    animasyon: IkonAnimasyonTuru
    renk_rolu: IkonRenkRolu
    animasyon_suresi_ms: int
    tekrarli: bool
    parlaklik: float
    saydamlik: float
    olcek: float

    def __post_init__(self) -> None:
        if self.animasyon_suresi_ms < 0:
            raise ValueError(
                "animasyon_suresi_ms negatif olamaz."
            )

        if not 0.0 <= self.parlaklik <= 2.0:
            raise ValueError(
                "parlaklik 0.0 ile 2.0 arasında olmalıdır."
            )

        if not 0.0 <= self.saydamlik <= 1.0:
            raise ValueError(
                "saydamlik 0.0 ile 1.0 arasında olmalıdır."
            )

        if not 0.5 <= self.olcek <= 2.0:
            raise ValueError(
                "olcek 0.5 ile 2.0 arasında olmalıdır."
            )


@dataclass(frozen=True, slots=True)
class IkonDurumDegisimi:
    """Bir ikonun durum geçiş kaydı."""

    ikon_kimligi: str
    onceki_durum: IkonCalismaDurumu
    yeni_durum: IkonCalismaDurumu
    neden: str
    oncelik: IkonOnceligi = IkonOnceligi.NORMAL
    zaman: datetime = field(default_factory=simdi)
    ek_veri: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ikon_kimligi.strip():
            raise ValueError("ikon_kimligi boş olamaz.")

        if not self.neden.strip():
            raise ValueError("neden boş olamaz.")


@dataclass(slots=True)
class IkonRuntimeKaydi:
    """Tek bir UGR ikonunun canlı çalışma kaydı."""

    ikon_kimligi: str
    kategori: str
    dosya_yolu: str
    etiket: str
    durum: IkonCalismaDurumu = IkonCalismaDurumu.BEKLIYOR
    gorunum_modu: IkonGorunumModu = IkonGorunumModu.MOD_2B
    bagli_nesne_kimligi: str | None = None
    aktif: bool = True
    son_guncelleme: datetime = field(default_factory=simdi)
    meta_veri: dict[str, Any] = field(default_factory=dict)
    gecmis: list[IkonDurumDegisimi] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.ikon_kimligi.strip():
            raise ValueError("ikon_kimligi boş olamaz.")

        if not self.kategori.strip():
            raise ValueError("kategori boş olamaz.")

        if not self.dosya_yolu.strip():
            raise ValueError("dosya_yolu boş olamaz.")

        if not self.etiket.strip():
            raise ValueError("etiket boş olamaz.")

    def durum_degistir(
        self,
        *,
        yeni_durum: IkonCalismaDurumu,
        neden: str,
        oncelik: IkonOnceligi = IkonOnceligi.NORMAL,
        ek_veri: dict[str, Any] | None = None,
    ) -> IkonDurumDegisimi:
        """İkon durumunu değiştirir ve geçmişe kaydeder."""

        degisim = IkonDurumDegisimi(
            ikon_kimligi=self.ikon_kimligi,
            onceki_durum=self.durum,
            yeni_durum=yeni_durum,
            neden=neden,
            oncelik=oncelik,
            ek_veri=dict(ek_veri or {}),
        )

        self.durum = yeni_durum
        self.son_guncelleme = degisim.zaman
        self.gecmis.append(degisim)

        return degisim

    def gorunum_modu_degistir(
        self,
        gorunum_modu: IkonGorunumModu,
    ) -> None:
        """İkonun 2B, 3B veya AR görünümünü değiştirir."""

        self.gorunum_modu = gorunum_modu
        self.son_guncelleme = simdi()

    def ozet(self) -> dict[str, Any]:
        """Türkçe anahtarlarla güvenli özet üretir."""

        return {
            "ikon_kimligi": self.ikon_kimligi,
            "kategori": self.kategori,
            "etiket": self.etiket,
            "dosya_yolu": self.dosya_yolu,
            "durum": self.durum.value,
            "gorunum_modu": self.gorunum_modu.value,
            "bagli_nesne_kimligi": self.bagli_nesne_kimligi,
            "aktif": self.aktif,
            "son_guncelleme": self.son_guncelleme.isoformat(),
            "durum_gecmisi_sayisi": len(self.gecmis),
            "meta_veri": dict(self.meta_veri),
        }
