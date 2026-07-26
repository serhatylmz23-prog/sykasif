from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .otonomi import BilgeKaanKontrolluOtonom, Karar


class BaglantiTuru(StrEnum):
    KUMANDA = "kumanda"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    KABLOLU = "kablolu"


class CihazTuru(StrEnum):
    YILAN_KAMERA = "yilan_kamera"
    DRONE = "drone"
    MINI_ROBOT = "mini_robot"
    KAMERA = "kamera"
    ISIK = "isik"
    SENSOR = "sensor"


class EylemTuru(StrEnum):
    SAGA_DON = "saga_don"
    SOLA_DON = "sola_don"
    YUKARI = "yukari"
    ASAGI = "asagi"
    ILERI = "ileri"
    GERI = "geri"
    DUR = "dur"
    GERI_CAGIR = "geri_cagir"
    ACIL_DURDUR = "acil_durdur"
    OTONOM_BASLAT = "otonom_baslat"
    OTONOM_BITIR = "otonom_bitir"
    FREKANS_DEGISTIR = "frekans_degistir"
    MOR_ISIK_AC = "mor_isik_ac"
    MOR_ISIK_KAPAT = "mor_isik_kapat"


class KararSinifi(StrEnum):
    ANLIK_EYLEM = "anlik_eylem"
    SISTEMSEL_DEGISIKLIK = "sistemsel_degisiklik"


@dataclass(frozen=True)
class CihazProfili:
    cihaz_id: str
    cihaz_turu: CihazTuru
    baglanti_turleri: tuple[BaglantiTuru, ...]
    desteklenen_eylemler: tuple[EylemTuru, ...]
    adaptoru_var: bool
    bagli: bool = False

    def eylemi_destekler(self, eylem: EylemTuru) -> bool:
        return self.adaptoru_var and self.bagli and eylem in self.desteklenen_eylemler


@dataclass(frozen=True)
class EylemIstegi:
    cihaz_id: str
    eylem: EylemTuru
    karar_sinifi: KararSinifi
    parametreler: dict[str, float | int | str] = field(default_factory=dict)
    gerekce: str = ""


@dataclass(frozen=True)
class EylemSonucu:
    karar: Karar
    uygulanabilir: bool
    gerekce: str
    cihaz_id: str
    eylem: EylemTuru


@dataclass
class OneriVeEylemKatmani:
    bilge_kaan: BilgeKaanKontrolluOtonom
    cihazlar: dict[str, CihazProfili] = field(default_factory=dict)
    olay_kaydi: list[dict[str, Any]] = field(default_factory=list)

    def cihaz_ekle(self, profil: CihazProfili) -> None:
        self.cihazlar[profil.cihaz_id] = profil

    def degerlendir(self, istek: EylemIstegi) -> EylemSonucu:
        cihaz = self.cihazlar.get(istek.cihaz_id)
        if cihaz is None:
            return self._sonuc(istek, Karar.EK_VERI, False, "Cihaz profili bulunamadı")
        if not cihaz.eylemi_destekler(istek.eylem):
            return self._sonuc(istek, Karar.EK_VERI, False, "Cihaz bağlı değil, adaptörü yok veya eylem desteklenmiyor")

        if istek.eylem == EylemTuru.ACIL_DURDUR:
            return self._sonuc(istek, Karar.ONAY, True, "Acil durdurma doğrudan uygulanabilir")

        if istek.karar_sinifi == KararSinifi.SISTEMSEL_DEGISIKLIK:
            return self._sonuc(
                istek,
                Karar.EK_VERI,
                False,
                "Büyük ve kalıcı sistem değişikliklerinde ekosistem yalnız öneri sunabilir",
            )

        sayisal = {k: float(v) for k, v in istek.parametreler.items() if isinstance(v, (int, float))}
        karar = self.bilge_kaan.degerlendir("arastirma_prototipi", sayisal)
        if karar != Karar.ONAY:
            return self._sonuc(istek, karar, False, "Anlık eylem Bilge Kaan onaylı sınırların dışında")
        return self._sonuc(istek, Karar.ONAY, True, "Anlık eylem Bilge Kaan onaylı sınırlar içinde")

    def _sonuc(self, istek: EylemIstegi, karar: Karar, uygulanabilir: bool, gerekce: str) -> EylemSonucu:
        kayit = {
            "cihaz_id": istek.cihaz_id,
            "eylem": istek.eylem,
            "karar": karar,
            "uygulanabilir": uygulanabilir,
            "gerekce": gerekce,
        }
        self.olay_kaydi.append(kayit)
        return EylemSonucu(karar, uygulanabilir, gerekce, istek.cihaz_id, istek.eylem)
