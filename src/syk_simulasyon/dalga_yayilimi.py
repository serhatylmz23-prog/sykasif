from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import random
from typing import Sequence

from .dalga_denklemleri import gidis_donus_gecikmesi_s, sinuz_ornegi
from .zayiflama_modeli import ZayiflamaGirdisi, ZayiflamaModeli
from .ortam_modeli import OrtamModeli, ortak_girdileri_dogrula
from .gurultu_modeli import GurultuModeli, GurultuProfili


@dataclass(frozen=True, slots=True)
class SanalHamSinyal:
    simülasyon_kimligi: str
    zaman_s: tuple[float, ...]
    genlik: tuple[float, ...]
    gecikme_s: float
    kullanılan_varsayimlar: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DalgaYayilimGirdisi:
    ortam: OrtamModeli
    derinlik_m: float
    frekans_hz: float
    ornekleme_hz: float
    sure_s: float
    baslangic_genligi: float = 1.0
    yansima_katsayisi: float = 1.0
    faz_rad: float = 0.0
    gurultu_std: float = 0.0
    rastgele_tohum: int = 0
    gurultu_profili: GurultuProfili | None = None
    geometrik_yayilim: bool = False
    geometrik_us: float = 1.0
    referans_mesafe_m: float = 1.0

    def dogrula(self) -> None:
        self.ortam.dogrula()
        ortak_girdileri_dogrula(
            derinlik_m=self.derinlik_m,
            frekans_hz=self.frekans_hz,
            ornekleme_hz=self.ornekleme_hz,
        )
        if self.sure_s <= 0:
            raise ValueError("sure_s pozitif olmalıdır")
        if self.baslangic_genligi < 0:
            raise ValueError("baslangic_genligi negatif olamaz")
        if not 0.0 <= self.yansima_katsayisi <= 1.0:
            raise ValueError("yansima_katsayisi 0 ile 1 arasında olmalıdır")
        if self.gurultu_std < 0:
            raise ValueError("gurultu_std negatif olamaz")
        if self.geometrik_us < 0:
            raise ValueError("geometrik_us negatif olamaz")
        if self.referans_mesafe_m <= 0:
            raise ValueError("referans_mesafe_m pozitif olmalıdır")


class DalgaYayilimMotoru:
    """0–2,25 m aralığı için doğrulanabilir ilk sentetik dalga üreticisi.

    Model homojen ortam, düzlemsel hedef, tek yansıma ve sabit zayıflama
    varsayımlarını kullanır. Gerçek sonar/metal/mineral cihaz modeli değildir.
    """

    VARSAYIMLAR = (
        "homojen_ortam",
        "duzlemsel_hedef",
        "tek_yansima",
        "sabit_db_m_zayiflama",
    )

    def uret(self, girdi: DalgaYayilimGirdisi) -> SanalHamSinyal:
        girdi.dogrula()
        adet = max(1, int(round(girdi.sure_s * girdi.ornekleme_hz)))
        zaman = tuple(i / girdi.ornekleme_hz for i in range(adet))
        gecikme = gidis_donus_gecikmesi_s(girdi.derinlik_m, girdi.ortam.yayilim_hizi_m_s)
        zayiflama = ZayiflamaModeli().hesapla(ZayiflamaGirdisi(
            tek_yon_mesafe_m=girdi.derinlik_m,
            ortam_zayiflama_db_m=girdi.ortam.zayiflama_db_m,
            gidis_donus=True,
            geometrik_yayilim=girdi.geometrik_yayilim,
            referans_mesafe_m=girdi.referans_mesafe_m,
            geometrik_us=girdi.geometrik_us,
        ))
        genlik_katsayisi = zayiflama.genlik_katsayisi
        tepe_genlik = girdi.baslangic_genligi * girdi.yansima_katsayisi * genlik_katsayisi
        rng = random.Random(girdi.rastgele_tohum)

        temiz_ornekler: list[float] = []
        for t in zaman:
            if t < gecikme:
                deger = 0.0
            else:
                deger = sinuz_ornegi(
                    genlik=tepe_genlik,
                    frekans_hz=girdi.frekans_hz,
                    zaman_s=t - gecikme,
                    faz_rad=girdi.faz_rad,
                )
            if girdi.gurultu_std:
                deger += rng.gauss(0.0, girdi.gurultu_std)
            temiz_ornekler.append(deger)

        if girdi.gurultu_profili is not None:
            ornekler = list(GurultuModeli().uygula(
                temiz_ornekler,
                ornekleme_hz=girdi.ornekleme_hz,
                profil=girdi.gurultu_profili,
            ).genlik)
        else:
            ornekler = temiz_ornekler

        kimlik_malzeme = repr(girdi).encode("utf-8")
        kimlik = "SS-" + hashlib.sha256(kimlik_malzeme).hexdigest()[:16].upper()
        return SanalHamSinyal(
            simülasyon_kimligi=kimlik,
            zaman_s=zaman,
            genlik=tuple(ornekler),
            gecikme_s=gecikme,
            kullanılan_varsayimlar=self.VARSAYIMLAR,
        )
