from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum


class GorselSorun(StrEnum):
    NETLIK_DUSUK = "netlik_dusuk"
    TITRESIM_YUKSEK = "titresim_yuksek"
    ISIK_YETERSIZ = "isik_yetersiz"
    YANSIMA_YUKSEK = "yansima_yuksek"
    GORUNTU_KAYBI = "goruntu_kaybi"
    ODAK_BOZUK = "odak_bozuk"


@dataclass(frozen=True)
class GorselKaliteOlcumu:
    netlik: float
    titresim: float
    isik: float
    yansima: float
    goruntu_var: bool
    odak: float

    def __post_init__(self) -> None:
        for alan in ("netlik", "titresim", "isik", "yansima", "odak"):
            deger = getattr(self, alan)
            if not 0.0 <= deger <= 1.0:
                raise ValueError(f"{alan} 0 ile 1 arasında olmalıdır")


@dataclass(frozen=True)
class GorselKaliteSonucu:
    sorunlar: tuple[GorselSorun, ...]
    kalite_puani: float
    oneriler: tuple[str, ...]


class GorselEDSAnalizcisi:
    """Canlı insan veya yüz tanıma yapmadan görüntü kalitesini denetler."""

    def analiz_et(self, olcum: GorselKaliteOlcumu) -> GorselKaliteSonucu:
        sorunlar: list[GorselSorun] = []
        oneriler: list[str] = []
        if not olcum.goruntu_var:
            sorunlar.append(GorselSorun.GORUNTU_KAYBI)
            oneriler.append("Kamera bağlantısını kontrol et")
        if olcum.netlik < 0.55:
            sorunlar.append(GorselSorun.NETLIK_DUSUK)
            oneriler.append("Kamerayı sabitle veya netliği artır")
        if olcum.titresim > 0.45:
            sorunlar.append(GorselSorun.TITRESIM_YUKSEK)
            oneriler.append("Hareketi yavaşlat veya kamerayı sabitle")
        if olcum.isik < 0.40:
            sorunlar.append(GorselSorun.ISIK_YETERSIZ)
            oneriler.append("Uygun yardımcı ışığı aç")
        if olcum.yansima > 0.60:
            sorunlar.append(GorselSorun.YANSIMA_YUKSEK)
            oneriler.append("Kamera veya ışık açısını değiştir")
        if olcum.odak < 0.55:
            sorunlar.append(GorselSorun.ODAK_BOZUK)
            oneriler.append("Odağı yeniden ayarla")

        puan = (
            olcum.netlik * 0.25
            + (1 - olcum.titresim) * 0.20
            + olcum.isik * 0.15
            + (1 - olcum.yansima) * 0.15
            + olcum.odak * 0.20
            + (0.05 if olcum.goruntu_var else 0.0)
        )
        return GorselKaliteSonucu(tuple(sorunlar), round(max(0.0, min(1.0, puan)), 4), tuple(oneriler))
