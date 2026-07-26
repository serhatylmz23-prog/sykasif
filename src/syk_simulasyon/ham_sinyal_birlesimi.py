from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Mapping, Sequence


def _dogrula_sonlu(dizi: Sequence[float], ad: str) -> tuple[float, ...]:
    if not dizi:
        raise ValueError(f"{ad} boş olamaz")
    sonuc = tuple(float(x) for x in dizi)
    if any(not math.isfinite(x) for x in sonuc):
        raise ValueError(f"{ad} yalnız sonlu sayılar içermelidir")
    return sonuc


@dataclass(frozen=True, slots=True)
class SinyalBileseni:
    ad: str
    genlik: tuple[float, ...]
    ornekleme_hz: float
    baslangic_s: float = 0.0

    def __post_init__(self) -> None:
        if not self.ad.strip():
            raise ValueError("bileşen adı boş olamaz")
        object.__setattr__(self, "genlik", _dogrula_sonlu(self.genlik, "genlik"))
        if self.ornekleme_hz <= 0:
            raise ValueError("ornekleme_hz pozitif olmalıdır")
        if not math.isfinite(self.baslangic_s):
            raise ValueError("baslangic_s sonlu olmalıdır")

    @property
    def sure_s(self) -> float:
        return len(self.genlik) / self.ornekleme_hz


@dataclass(frozen=True, slots=True)
class HamSinyalUstVerisi:
    arastirma_kimligi: str
    deney_numarasi: str
    simulasyon_kimligi: str
    ftsu_surumu: str
    rastgele_tohum: int
    parametre_ozeti: Mapping[str, object]
    olusturma_zamani_utc: str

    def __post_init__(self) -> None:
        for ad in ("arastirma_kimligi", "deney_numarasi", "simulasyon_kimligi", "ftsu_surumu"):
            if not str(getattr(self, ad)).strip():
                raise ValueError(f"{ad} boş olamaz")


@dataclass(frozen=True, slots=True)
class HamSinyal:
    zaman_s: tuple[float, ...]
    genlik: tuple[float, ...]
    ornekleme_hz: float
    ust_veri: HamSinyalUstVerisi
    kaynak_bilesenler: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.zaman_s) != len(self.genlik):
            raise ValueError("zaman ve genlik uzunlukları eşit olmalıdır")
        if not self.zaman_s:
            raise ValueError("ham sinyal boş olamaz")
        if any(not math.isfinite(x) for x in self.zaman_s + self.genlik):
            raise ValueError("ham sinyal yalnız sonlu sayılar içermelidir")
        if any(b <= a for a, b in zip(self.zaman_s, self.zaman_s[1:])):
            raise ValueError("zaman ekseni kesin artan olmalıdır")


class ZamanEsleyici:
    """Bileşenleri ortak örnekleme hızına doğrusal enterpolasyonla taşır."""

    @staticmethod
    def yeniden_ornekle(
        bilesen: SinyalBileseni,
        *,
        hedef_ornekleme_hz: float,
        hedef_baslangic_s: float,
        hedef_ornek_sayisi: int,
    ) -> tuple[float, ...]:
        if hedef_ornekleme_hz <= 0:
            raise ValueError("hedef_ornekleme_hz pozitif olmalıdır")
        if hedef_ornek_sayisi <= 0:
            raise ValueError("hedef_ornek_sayisi pozitif olmalıdır")

        cikti: list[float] = []
        son_index = len(bilesen.genlik) - 1
        bitis_s = bilesen.baslangic_s + son_index / bilesen.ornekleme_hz

        for i in range(hedef_ornek_sayisi):
            t = hedef_baslangic_s + i / hedef_ornekleme_hz
            if t < bilesen.baslangic_s or t > bitis_s:
                cikti.append(0.0)
                continue

            konum = (t - bilesen.baslangic_s) * bilesen.ornekleme_hz
            sol = int(math.floor(konum))
            sag = min(sol + 1, son_index)
            oran = konum - sol
            deger = bilesen.genlik[sol] * (1.0 - oran) + bilesen.genlik[sag] * oran
            cikti.append(deger)

        return tuple(cikti)


class SimulasyonKimligiUretici:
    """Aynı girdi ve tohum için aynı kodlanmış kimliği üretir."""

    @staticmethod
    def uret(
        *,
        arastirma_kimligi: str,
        deney_numarasi: str,
        ftsu_surumu: str,
        rastgele_tohum: int,
        parametre_ozeti: Mapping[str, object],
    ) -> str:
        if not arastirma_kimligi.strip() or not deney_numarasi.strip():
            raise ValueError("araştırma kimliği ve deney numarası zorunludur")
        belge = {
            "ak": arastirma_kimligi,
            "dn": deney_numarasi,
            "surum": ftsu_surumu,
            "tohum": rastgele_tohum,
            "parametreler": parametre_ozeti,
        }
        ham = json.dumps(belge, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return "SIM-" + hashlib.sha256(ham.encode("utf-8")).hexdigest()[:20].upper()


class HamSinyalBirlesimMotoru:
    """Farklı örnekleme hızlarındaki sinyal bileşenlerini ortak eksende toplar."""

    def birlestir(
        self,
        bilesenler: Sequence[SinyalBileseni],
        *,
        hedef_ornekleme_hz: float | None = None,
        kirpma_siniri: float | None = None,
        arastirma_kimligi: str,
        deney_numarasi: str,
        ftsu_surumu: str,
        rastgele_tohum: int,
        parametre_ozeti: Mapping[str, object],
        olusturma_zamani_utc: str | None = None,
    ) -> HamSinyal:
        if not bilesenler:
            raise ValueError("en az bir sinyal bileşeni gereklidir")
        if len({b.ad for b in bilesenler}) != len(bilesenler):
            raise ValueError("bileşen adları benzersiz olmalıdır")

        hedef_hz = hedef_ornekleme_hz or max(b.ornekleme_hz for b in bilesenler)
        if hedef_hz <= 0:
            raise ValueError("hedef_ornekleme_hz pozitif olmalıdır")
        if kirpma_siniri is not None and kirpma_siniri <= 0:
            raise ValueError("kirpma_siniri pozitif olmalıdır")

        baslangic = min(b.baslangic_s for b in bilesenler)
        bitis = max(b.baslangic_s + (len(b.genlik) - 1) / b.ornekleme_hz for b in bilesenler)
        ornek_sayisi = int(round((bitis - baslangic) * hedef_hz)) + 1
        zaman = tuple(baslangic + i / hedef_hz for i in range(ornek_sayisi))

        eslenmis = [
            ZamanEsleyici.yeniden_ornekle(
                b,
                hedef_ornekleme_hz=hedef_hz,
                hedef_baslangic_s=baslangic,
                hedef_ornek_sayisi=ornek_sayisi,
            )
            for b in bilesenler
        ]
        toplam = [sum(dizi[i] for dizi in eslenmis) for i in range(ornek_sayisi)]

        if kirpma_siniri is not None:
            toplam = [max(-kirpma_siniri, min(kirpma_siniri, x)) for x in toplam]

        simulasyon_kimligi = SimulasyonKimligiUretici.uret(
            arastirma_kimligi=arastirma_kimligi,
            deney_numarasi=deney_numarasi,
            ftsu_surumu=ftsu_surumu,
            rastgele_tohum=rastgele_tohum,
            parametre_ozeti=parametre_ozeti,
        )
        zaman_utc = olusturma_zamani_utc or datetime.now(timezone.utc).isoformat()
        ust_veri = HamSinyalUstVerisi(
            arastirma_kimligi=arastirma_kimligi,
            deney_numarasi=deney_numarasi,
            simulasyon_kimligi=simulasyon_kimligi,
            ftsu_surumu=ftsu_surumu,
            rastgele_tohum=rastgele_tohum,
            parametre_ozeti=dict(parametre_ozeti),
            olusturma_zamani_utc=zaman_utc,
        )
        return HamSinyal(
            zaman_s=zaman,
            genlik=tuple(toplam),
            ornekleme_hz=hedef_hz,
            ust_veri=ust_veri,
            kaynak_bilesenler=tuple(b.ad for b in bilesenler),
        )
