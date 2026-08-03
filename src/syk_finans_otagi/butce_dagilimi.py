from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .portfoy_analizi import (
    VarlikAdayi,
)


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.01")
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
        4,
    )


@dataclass(frozen=True, slots=True)
class VarlikButcePayi:
    sembol: str
    ayrilan_tutar: Decimal
    butce_orani: float
    dagitim_puani: float
    guven_endeksi: float
    kanit_gucu: float
    risk_puani: float
    kullanici_katsayisi: float
    gerekce: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "ayrilan_tutar": float(
                self.ayrilan_tutar
            ),
            "butce_orani": round(
                self.butce_orani,
                3,
            ),
            "dagitim_puani": round(
                self.dagitim_puani,
                4,
            ),
            "guven_endeksi": round(
                self.guven_endeksi,
                3,
            ),
            "kanit_gucu": round(
                self.kanit_gucu,
                3,
            ),
            "risk_puani": round(
                self.risk_puani,
                3,
            ),
            "kullanici_katsayisi": round(
                self.kullanici_katsayisi,
                3,
            ),
            "gerekce": self.gerekce,
        }


@dataclass(frozen=True, slots=True)
class ButceDagilimPlani:
    toplam_butce: Decimal
    yatirima_ayrilan_butce: Decimal
    nakit_guvenlik_payi: Decimal
    nakit_guvenlik_orani: float
    paylar: tuple[VarlikButcePayi, ...]
    kullanilan_tutar: Decimal
    yuvarlama_artigi: Decimal
    dagitim_sha256: str

    @property
    def secilen_varlik_sayisi(self) -> int:
        return len(
            self.paylar
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "toplam_butce": float(
                self.toplam_butce
            ),
            "yatirima_ayrilan_butce": float(
                self.yatirima_ayrilan_butce
            ),
            "nakit_guvenlik_payi": float(
                self.nakit_guvenlik_payi
            ),
            "nakit_guvenlik_orani": round(
                self.nakit_guvenlik_orani,
                3,
            ),
            "kullanilan_tutar": float(
                self.kullanilan_tutar
            ),
            "yuvarlama_artigi": float(
                self.yuvarlama_artigi
            ),
            "secilen_varlik_sayisi": (
                self.secilen_varlik_sayisi
            ),
            "paylar": [
                pay.as_dict()
                for pay in self.paylar
            ],
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
            "dagitim_sha256": (
                self.dagitim_sha256
            ),
        }


class ButceDagilimMotoru:
    MAKSIMUM_VARLIK = 7

    @classmethod
    def dagit(
        cls,
        *,
        toplam_butce: Decimal | int | float | str,
        secilenler: Iterable[VarlikAdayi],
        nakit_guvenlik_orani: float = 10.0,
        kullanici_katsayilari: (
            Mapping[str, float] | None
        ) = None,
        minimum_varlik_tutari: (
            Decimal | int | float | str
        ) = 100.0,
    ) -> ButceDagilimPlani:
        butce = _para(
            toplam_butce
        )

        if butce <= 0:
            raise ValueError(
                "Toplam yatırım bütçesi "
                "pozitif olmalıdır."
            )

        adaylar = tuple(
            secilenler
        )

        if not adaylar:
            raise ValueError(
                "Bütçe dağıtılacak varlık "
                "seçilmedi."
            )

        if len(adaylar) > cls.MAKSIMUM_VARLIK:
            raise ValueError(
                "En fazla 7 varlığa "
                "bütçe dağıtılabilir."
            )

        semboller = [
            aday.sembol.strip().upper()
            for aday in adaylar
        ]

        if len(set(semboller)) != len(
            semboller
        ):
            raise ValueError(
                "Aynı varlık birden fazla "
                "seçilemez."
            )

        guvenlik_orani = _sinirla(
            nakit_guvenlik_orani,
            alt=0.0,
            ust=50.0,
        )

        nakit = _para(
            butce
            * Decimal(
                str(guvenlik_orani)
            )
            / Decimal("100")
        )

        yatirim_butcesi = _para(
            butce - nakit
        )

        minimum_tutar = _para(
            minimum_varlik_tutari
        )

        if minimum_tutar <= 0:
            raise ValueError(
                "Asgari varlık tutarı "
                "pozitif olmalıdır."
            )

        if (
            minimum_tutar
            * len(adaylar)
            > yatirim_butcesi
        ):
            raise ValueError(
                "Yatırım bütçesi seçilen "
                "varlıkların asgari tutarını "
                "karşılamıyor."
            )

        katsayilar = {
            str(sembol).strip().upper(): (
                float(katsayi)
            )
            for sembol, katsayi
            in (
                kullanici_katsayilari
                or {}
            ).items()
        }

        puanlar: list[
            tuple[
                VarlikAdayi,
                float,
                float,
            ]
        ] = []

        for aday in adaylar:
            sembol = (
                aday.sembol
                .strip()
                .upper()
            )

            kullanici_katsayisi = (
                katsayilar.get(
                    sembol,
                    1.0,
                )
            )

            if (
                kullanici_katsayisi
                <= 0
                or kullanici_katsayisi
                > 3.0
            ):
                raise ValueError(
                    "Kullanıcı katsayısı "
                    "0 ile 3 arasında olmalıdır: "
                    f"{sembol}"
                )

            risk_katsayisi = max(
                0.10,
                (
                    100.0
                    - _sinirla(
                        aday.risk_puani
                    )
                )
                / 100.0,
            )

            kanit_katsayisi = (
                _sinirla(
                    aday.kanit_gucu
                )
                / 100.0
            )

            guven_katsayisi = (
                _sinirla(
                    aday.guven_endeksi
                )
                / 100.0
            )

            taban_puan = (
                guven_katsayisi
                * 0.50
                + kanit_katsayisi
                * 0.30
                + risk_katsayisi
                * 0.20
            )

            yogunlasma_katsayisi = max(
                0.40,
                1.0
                - (
                    aday.yogunlasma_cezasi
                    / 100.0
                ),
            )

            dagitim_puani = (
                taban_puan
                * kullanici_katsayisi
                * yogunlasma_katsayisi
            )

            puanlar.append(
                (
                    aday,
                    dagitim_puani,
                    kullanici_katsayisi,
                )
            )

        toplam_puan = sum(
            puan
            for _, puan, _
            in puanlar
        )

        if toplam_puan <= 0:
            raise ValueError(
                "Bütçe dağılımı için "
                "geçerli puan üretilemedi."
            )

        asgari_toplam = _para(
            minimum_tutar
            * len(adaylar)
        )

        serbest_butce = _para(
            yatirim_butcesi
            - asgari_toplam
        )

        paylar: list[
            VarlikButcePayi
        ] = []

        kullanilan = Decimal(
            "0.00"
        )

        for aday, puan, katsayi in puanlar:
            oransal_ek = (
                serbest_butce
                * Decimal(
                    str(
                        puan
                        / toplam_puan
                    )
                )
            )

            ayrilan = (
                minimum_tutar
                + oransal_ek
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_DOWN,
            )

            kullanilan += ayrilan

            butce_orani = (
                float(
                    ayrilan
                    / yatirim_butcesi
                    * Decimal("100")
                )
                if yatirim_butcesi > 0
                else 0.0
            )

            gerekce = (
                f"Güven {aday.guven_endeksi:.1f}, "
                f"Kanıt Gücü {aday.kanit_gucu:.1f}, "
                f"Risk {aday.risk_puani:.1f}"
            )

            if katsayi != 1.0:
                gerekce += (
                    " ve kullanıcı tercihi "
                    f"{katsayi:.2f} katsayısı"
                )

            paylar.append(
                VarlikButcePayi(
                    sembol=(
                        aday.sembol
                        .strip()
                        .upper()
                    ),
                    ayrilan_tutar=_para(
                        ayrilan
                    ),
                    butce_orani=(
                        butce_orani
                    ),
                    dagitim_puani=puan,
                    guven_endeksi=(
                        aday.guven_endeksi
                    ),
                    kanit_gucu=(
                        aday.kanit_gucu
                    ),
                    risk_puani=(
                        aday.risk_puani
                    ),
                    kullanici_katsayisi=(
                        katsayi
                    ),
                    gerekce=gerekce,
                )
            )

        kullanilan = _para(
            kullanilan
        )

        artik = _para(
            yatirim_butcesi
            - kullanilan
        )

        paylar = sorted(
            paylar,
            key=lambda pay: (
                pay.ayrilan_tutar,
                pay.dagitim_puani,
            ),
            reverse=True,
        )

        kanit = {
            "toplam_butce": str(
                butce
            ),
            "yatirim_butcesi": str(
                yatirim_butcesi
            ),
            "nakit": str(
                nakit
            ),
            "guvenlik_orani": (
                guvenlik_orani
            ),
            "paylar": [
                {
                    "sembol": pay.sembol,
                    "ayrilan_tutar": str(
                        pay.ayrilan_tutar
                    ),
                    "butce_orani": round(
                        pay.butce_orani,
                        4,
                    ),
                    "dagitim_puani": round(
                        pay.dagitim_puani,
                        6,
                    ),
                }
                for pay in paylar
            ],
            "artik": str(
                artik
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return ButceDagilimPlani(
            toplam_butce=butce,
            yatirima_ayrilan_butce=(
                yatirim_butcesi
            ),
            nakit_guvenlik_payi=nakit,
            nakit_guvenlik_orani=(
                guvenlik_orani
            ),
            paylar=tuple(
                paylar
            ),
            kullanilan_tutar=(
                kullanilan
            ),
            yuvarlama_artigi=artik,
            dagitim_sha256=sha256(
                kodlu
            ).hexdigest(),
        )