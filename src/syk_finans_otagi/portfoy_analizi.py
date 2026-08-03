from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable

from .modeller import (
    VarlikTuru,
    YatirimKosulu,
)


def _sinirla(
    deger: float,
    alt: float = 0.0,
    ust: float = 100.0,
) -> float:
    return round(
        min(
            ust,
            max(
                alt,
                float(deger),
            ),
        ),
        3,
    )


@dataclass(frozen=True, slots=True)
class Kanit:
    kanit_id: str
    baslik: str
    deger: float
    agirlik: float
    kaynak: str
    guncellik: str
    olumlu: bool
    aciklama: str

    @property
    def agirlikli_puan(self) -> float:
        yon = (
            1.0
            if self.olumlu
            else -1.0
        )

        return (
            float(self.deger)
            * float(self.agirlik)
            * yon
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kanit_id": self.kanit_id,
            "baslik": self.baslik,
            "deger": _sinirla(
                self.deger
            ),
            "agirlik": round(
                float(self.agirlik),
                4,
            ),
            "kaynak": self.kaynak,
            "guncellik": self.guncellik,
            "olumlu": self.olumlu,
            "aciklama": self.aciklama,
            "agirlikli_puan": round(
                self.agirlikli_puan,
                4,
            ),
        }


@dataclass(frozen=True, slots=True)
class VarlikAdayi:
    sembol: str
    varlik_turu: VarlikTuru
    sektor: str
    mevcut_fiyat: float
    kanitlar: tuple[Kanit, ...]
    risk_puani: float
    mevcut_portfoyde: bool = False
    mevcut_agirlik: float = 0.0

    @property
    def kanit_gucu(self) -> float:
        if not self.kanitlar:
            return 0.0

        toplam_agirlik = sum(
            abs(
                kanit.agirlik
            )
            for kanit in self.kanitlar
        )

        if toplam_agirlik <= 0:
            return 0.0

        kapsama = min(
            1.0,
            len(self.kanitlar) / 8.0,
        )

        ortalama_deger = sum(
            kanit.deger
            * abs(
                kanit.agirlik
            )
            for kanit in self.kanitlar
        ) / toplam_agirlik

        kaynak_sayisi = len(
            {
                kanit.kaynak
                for kanit in self.kanitlar
                if kanit.kaynak.strip()
            }
        )

        kaynak_cesitliligi = min(
            1.0,
            kaynak_sayisi / 5.0,
        )

        return _sinirla(
            ortalama_deger
            * 0.55
            + kapsama * 100 * 0.25
            + kaynak_cesitliligi
            * 100
            * 0.20
        )

    @property
    def temel_puan(self) -> float:
        if not self.kanitlar:
            return 0.0

        toplam_agirlik = sum(
            abs(
                kanit.agirlik
            )
            for kanit in self.kanitlar
        )

        if toplam_agirlik <= 0:
            return 0.0

        ham = sum(
            kanit.agirlikli_puan
            for kanit in self.kanitlar
        ) / toplam_agirlik

        return _sinirla(
            50.0 + ham / 2.0
        )

    @property
    def yogunlasma_cezasi(self) -> float:
        if not self.mevcut_portfoyde:
            return 0.0

        if self.mevcut_agirlik <= 15:
            return 0.0

        return _sinirla(
            (
                self.mevcut_agirlik
                - 15.0
            )
            * 1.6,
            ust=30.0,
        )

    @property
    def guven_endeksi(self) -> float:
        risk_cezasi = (
            _sinirla(
                self.risk_puani
            )
            * 0.28
        )

        kanit_destegi = (
            self.kanit_gucu
            * 0.32
        )

        temel_destek = (
            self.temel_puan
            * 0.68
        )

        return _sinirla(
            temel_destek
            + kanit_destegi
            - risk_cezasi
            - self.yogunlasma_cezasi
        )

    @property
    def karar(self) -> str:
        if (
            self.guven_endeksi >= 78
            and self.kanit_gucu >= 70
            and self.risk_puani <= 55
        ):
            return "olumlu_aday"

        if (
            self.guven_endeksi >= 60
            and self.kanit_gucu >= 50
        ):
            return "izle"

        if self.risk_puani >= 75:
            return "yuksek_risk"

        return "temkinli"

    @property
    def kisa_yorum(self) -> str:
        if self.karar == "olumlu_aday":
            return (
                "Mevcut kanıtlar birlikte "
                "değerlendirildiğinde olumlu aday."
            )

        if self.karar == "izle":
            return (
                "Görünüm izlemeye değer; "
                "yeni kanıt beklenmeli."
            )

        if self.karar == "yuksek_risk":
            return (
                "Olası getiriye rağmen risk "
                "seviyesi belirgin biçimde yüksek."
            )

        return (
            "Kanıtlar henüz güçlü ve tutarlı "
            "bir yön oluşturmuyor."
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "sektor": self.sektor,
            "mevcut_fiyat": float(
                self.mevcut_fiyat
            ),
            "risk_puani": _sinirla(
                self.risk_puani
            ),
            "kanit_gucu": (
                self.kanit_gucu
            ),
            "temel_puan": (
                self.temel_puan
            ),
            "guven_endeksi": (
                self.guven_endeksi
            ),
            "mevcut_portfoyde": (
                self.mevcut_portfoyde
            ),
            "mevcut_agirlik": round(
                float(
                    self.mevcut_agirlik
                ),
                3,
            ),
            "yogunlasma_cezasi": (
                self.yogunlasma_cezasi
            ),
            "karar": self.karar,
            "kisa_yorum": (
                self.kisa_yorum
            ),
            "kanitlar": [
                kanit.as_dict()
                for kanit in self.kanitlar
            ],
        }


@dataclass(frozen=True, slots=True)
class PortfoyDegerlendirmesi:
    yatirim_kosulu: YatirimKosulu
    toplam_butce: float
    adaylar: tuple[VarlikAdayi, ...]
    secilenler: tuple[VarlikAdayi, ...]
    portfoy_uyarilari: tuple[str, ...]
    degerlendirme_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "yatirim_kosulu": (
                self.yatirim_kosulu.value
            ),
            "toplam_butce": round(
                float(
                    self.toplam_butce
                ),
                2,
            ),
            "aday_sayisi": len(
                self.adaylar
            ),
            "secilen_sayisi": len(
                self.secilenler
            ),
            "secilenler": [
                aday.as_dict()
                for aday in self.secilenler
            ],
            "portfoy_uyarilari": list(
                self.portfoy_uyarilari
            ),
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
            "degerlendirme_sha256": (
                self.degerlendirme_sha256
            ),
        }


class PortfoyAnalizMotoru:
    MAKSIMUM_ADAY = 7

    @classmethod
    def degerlendir(
        cls,
        *,
        toplam_butce: float,
        yatirim_kosulu: YatirimKosulu,
        adaylar: Iterable[VarlikAdayi],
        maksimum_aday: int = 7,
    ) -> PortfoyDegerlendirmesi:
        butce = float(
            toplam_butce
        )

        if butce <= 0:
            raise ValueError(
                "Yatırım bütçesi pozitif olmalıdır."
            )

        sinir = int(
            maksimum_aday
        )

        if (
            sinir <= 0
            or sinir > cls.MAKSIMUM_ADAY
        ):
            raise ValueError(
                "Aday sayısı 1 ile 7 "
                "arasında olmalıdır."
            )

        aday_listesi = tuple(
            adaylar
        )

        if not aday_listesi:
            raise ValueError(
                "Değerlendirilecek aday bulunamadı."
            )

        sirali = sorted(
            aday_listesi,
            key=lambda aday: (
                aday.guven_endeksi,
                aday.kanit_gucu,
                -aday.risk_puani,
            ),
            reverse=True,
        )

        secilenler: list[
            VarlikAdayi
        ] = []

        sektor_sayilari: dict[
            str,
            int,
        ] = {}

        for aday in sirali:
            if len(secilenler) >= sinir:
                break

            sektor = (
                aday.sektor.strip()
                or "belirsiz"
            )

            mevcut_sektor_sayisi = (
                sektor_sayilari.get(
                    sektor,
                    0,
                )
            )

            if (
                mevcut_sektor_sayisi >= 2
                and len(sirali) > sinir
            ):
                continue

            secilenler.append(
                aday
            )

            sektor_sayilari[
                sektor
            ] = (
                mevcut_sektor_sayisi
                + 1
            )

        uyarilar: list[str] = []

        yuksek_agirliklilar = [
            aday
            for aday in aday_listesi
            if aday.mevcut_agirlik >= 30
        ]

        if yuksek_agirliklilar:
            semboller = ", ".join(
                aday.sembol
                for aday
                in yuksek_agirliklilar
            )

            uyarilar.append(
                "Portföy yoğunlaşması yüksek: "
                f"{semboller}."
            )

        yuksek_riskliler = [
            aday
            for aday in secilenler
            if aday.risk_puani >= 70
        ]

        if yuksek_riskliler:
            uyarilar.append(
                "Seçilen adaylar içinde yüksek "
                "riskli varlık bulunuyor."
            )

        if not any(
            aday.kanit_gucu >= 70
            for aday in secilenler
        ):
            uyarilar.append(
                "Hiçbir adayın Kanıt Gücü "
                "yüzde 70 seviyesine ulaşmadı."
            )

        kanit = {
            "yatirim_kosulu": (
                yatirim_kosulu.value
            ),
            "toplam_butce": round(
                butce,
                2,
            ),
            "secilenler": [
                {
                    "sembol": aday.sembol,
                    "guven_endeksi": (
                        aday.guven_endeksi
                    ),
                    "kanit_gucu": (
                        aday.kanit_gucu
                    ),
                    "risk_puani": (
                        aday.risk_puani
                    ),
                }
                for aday in secilenler
            ],
            "uyarilar": uyarilar,
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return PortfoyDegerlendirmesi(
            yatirim_kosulu=(
                yatirim_kosulu
            ),
            toplam_butce=butce,
            adaylar=aday_listesi,
            secilenler=tuple(
                secilenler
            ),
            portfoy_uyarilari=tuple(
                uyarilar
            ),
            degerlendirme_sha256=(
                sha256(
                    kodlu
                ).hexdigest()
            ),
        )