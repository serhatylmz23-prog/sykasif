from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping
from uuid import uuid4

from .butce_dagilimi import (
    ButceDagilimPlani,
)
from .kademe_plani import (
    KademePlani,
    KademePlaniMotoru,
)


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.01")
    )


@dataclass(frozen=True, slots=True)
class VarlikYatirimPlani:
    sembol: str
    ayrilan_butce: Decimal
    kademe_plani: KademePlani

    @property
    def planlanan_lot(self) -> int:
        return (
            self.kademe_plani
            .planlanan_lot
        )

    @property
    def gerceklesen_lot(self) -> int:
        return (
            self.kademe_plani
            .gerceklesen_lot
        )

    @property
    def gerceklesen_tutar(self) -> Decimal:
        return (
            self.kademe_plani
            .gerceklesen_tutar
        )

    @property
    def ortalama_maliyet(
        self,
    ) -> Decimal | None:
        return (
            self.kademe_plani
            .ortalama_maliyet
        )

    @property
    def basari_orani(self) -> float:
        return (
            self.kademe_plani
            .basari_orani
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "ayrilan_butce": float(
                self.ayrilan_butce
            ),
            "planlanan_lot": (
                self.planlanan_lot
            ),
            "gerceklesen_lot": (
                self.gerceklesen_lot
            ),
            "gerceklesen_tutar": float(
                self.gerceklesen_tutar
            ),
            "ortalama_maliyet": (
                float(
                    self.ortalama_maliyet
                )
                if self.ortalama_maliyet
                is not None
                else None
            ),
            "basari_orani": (
                self.basari_orani
            ),
            "kademe_plani": (
                self.kademe_plani
                .as_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class TopluYatirimPlani:
    toplu_plan_id: str
    toplam_butce: Decimal
    nakit_guvenlik_payi: Decimal
    varlik_planlari: tuple[
        VarlikYatirimPlani,
        ...
    ]
    toplu_plan_sha256: str

    @property
    def planlanan_toplam_tutar(
        self,
    ) -> Decimal:
        return _para(
            sum(
                (
                    plan.kademe_plani
                    .planlanan_tutar
                    for plan
                    in self.varlik_planlari
                ),
                Decimal("0.00"),
            )
        )

    @property
    def gerceklesen_toplam_tutar(
        self,
    ) -> Decimal:
        return _para(
            sum(
                (
                    plan.gerceklesen_tutar
                    for plan
                    in self.varlik_planlari
                ),
                Decimal("0.00"),
            )
        )

    @property
    def kalan_yatirim_butcesi(
        self,
    ) -> Decimal:
        yatirima_ayrilan = _para(
            self.toplam_butce
            - self.nakit_guvenlik_payi
        )

        return _para(
            max(
                Decimal("0.00"),
                yatirima_ayrilan
                - self.gerceklesen_toplam_tutar,
            )
        )

    @property
    def toplam_gerceklesme_orani(
        self,
    ) -> float:
        if (
            self.planlanan_toplam_tutar
            <= 0
        ):
            return 0.0

        oran = (
            self.gerceklesen_toplam_tutar
            / self.planlanan_toplam_tutar
            * Decimal("100")
        )

        return round(
            min(
                100.0,
                max(
                    0.0,
                    float(oran),
                ),
            ),
            3,
        )

    @property
    def genel_basari_orani(
        self,
    ) -> float:
        toplam_agirlik = sum(
            (
                plan.kademe_plani
                .planlanan_tutar
                for plan
                in self.varlik_planlari
            ),
            Decimal("0.00"),
        )

        if toplam_agirlik <= 0:
            return 0.0

        agirlikli = sum(
            (
                Decimal(
                    str(
                        plan.basari_orani
                    )
                )
                * plan.kademe_plani
                .planlanan_tutar
                for plan
                in self.varlik_planlari
            ),
            Decimal("0.00"),
        )

        return round(
            float(
                agirlikli
                / toplam_agirlik
            ),
            3,
        )

    @property
    def gerceklesen_varlik_sayisi(
        self,
    ) -> int:
        return sum(
            plan.gerceklesen_lot > 0
            for plan
            in self.varlik_planlari
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "toplu_plan_id": (
                self.toplu_plan_id
            ),
            "toplam_butce": float(
                self.toplam_butce
            ),
            "nakit_guvenlik_payi": float(
                self.nakit_guvenlik_payi
            ),
            "planlanan_toplam_tutar": float(
                self.planlanan_toplam_tutar
            ),
            "gerceklesen_toplam_tutar": float(
                self.gerceklesen_toplam_tutar
            ),
            "kalan_yatirim_butcesi": float(
                self.kalan_yatirim_butcesi
            ),
            "toplam_gerceklesme_orani": (
                self.toplam_gerceklesme_orani
            ),
            "genel_basari_orani": (
                self.genel_basari_orani
            ),
            "varlik_sayisi": len(
                self.varlik_planlari
            ),
            "gerceklesen_varlik_sayisi": (
                self.gerceklesen_varlik_sayisi
            ),
            "varlik_planlari": [
                plan.as_dict()
                for plan
                in self.varlik_planlari
            ],
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
            "toplu_plan_sha256": (
                self.toplu_plan_sha256
            ),
        }


class TopluYatirimPlaniMotoru:
    @classmethod
    def olustur(
        cls,
        *,
        butce_dagilimi: ButceDagilimPlani,
        fiyat_kademeleri: Mapping[
            str,
            Iterable[
                Decimal | int | float | str
            ],
        ],
        dagilim_oranlari: (
            Mapping[
                str,
                Iterable[
                    Decimal | int | float | str
                ],
            ]
            | None
        ) = None,
        islem_yonu: str = "alim",
    ) -> TopluYatirimPlani:
        if islem_yonu not in {
            "alim",
            "satim",
        }:
            raise ValueError(
                "İşlem yönü alım veya "
                "satım olmalıdır."
            )

        fiyat_haritasi = {
            str(
                sembol
            ).strip().upper(): tuple(
                fiyatlar
            )
            for sembol, fiyatlar
            in fiyat_kademeleri.items()
        }

        oran_haritasi = {
            str(
                sembol
            ).strip().upper(): tuple(
                oranlar
            )
            for sembol, oranlar
            in (
                dagilim_oranlari
                or {}
            ).items()
        }

        varlik_planlari: list[
            VarlikYatirimPlani
        ] = []

        for pay in butce_dagilimi.paylar:
            sembol = (
                pay.sembol
                .strip()
                .upper()
            )

            if sembol not in fiyat_haritasi:
                raise KeyError(
                    "Fiyat kademeleri "
                    f"bulunamadı: {sembol}"
                )

            fiyatlar = fiyat_haritasi[
                sembol
            ]

            if not fiyatlar:
                raise ValueError(
                    "En az bir fiyat "
                    f"kademesi gerekli: {sembol}"
                )

            referans_fiyat = next(
                iter(
                    fiyatlar
                )
            )

            plan = (
                KademePlaniMotoru
                .olustur(
                    plan_id=(
                        "SYF-KDM-"
                        f"{uuid4().hex[:18]}"
                    ),
                    sembol=sembol,
                    islem_yonu=islem_yonu,
                    toplam_butce=(
                        pay.ayrilan_tutar
                    ),
                    referans_fiyat=(
                        referans_fiyat
                    ),
                    fiyatlar=fiyatlar,
                    dagilim_oranlari=(
                        oran_haritasi.get(
                            sembol
                        )
                    ),
                    aciklama=(
                        "SyFinansOtağı toplu "
                        "yatırım planı"
                    ),
                )
            )

            varlik_planlari.append(
                VarlikYatirimPlani(
                    sembol=sembol,
                    ayrilan_butce=(
                        pay.ayrilan_tutar
                    ),
                    kademe_plani=plan,
                )
            )

        toplu_plan = TopluYatirimPlani(
            toplu_plan_id=(
                "SYF-TPL-"
                f"{uuid4().hex[:20]}"
            ),
            toplam_butce=(
                butce_dagilimi
                .toplam_butce
            ),
            nakit_guvenlik_payi=(
                butce_dagilimi
                .nakit_guvenlik_payi
            ),
            varlik_planlari=tuple(
                varlik_planlari
            ),
            toplu_plan_sha256="",
        )

        return cls.yeniden_muhurle(
            toplu_plan
        )

    @classmethod
    def kademe_durumu_degistir(
        cls,
        plan: TopluYatirimPlani,
        *,
        sembol: str,
        kademe_no: int,
        gerceklesti: bool,
        gerceklesen_fiyat: (
            Decimal | int | float | str | None
        ) = None,
        gerceklesen_lot: int | None = None,
    ) -> TopluYatirimPlani:
        aranan = (
            str(
                sembol
            )
            .strip()
            .upper()
        )

        bulundu = False
        yeni_planlar: list[
            VarlikYatirimPlani
        ] = []

        for varlik_plani in (
            plan.varlik_planlari
        ):
            if (
                varlik_plani.sembol
                != aranan
            ):
                yeni_planlar.append(
                    varlik_plani
                )
                continue

            bulundu = True

            yeni_kademe_plani = (
                varlik_plani
                .kademe_plani
                .kademe_guncelle(
                    kademe_no,
                    gerceklesti=(
                        gerceklesti
                    ),
                    gerceklesen_fiyat=(
                        gerceklesen_fiyat
                    ),
                    gerceklesen_lot=(
                        gerceklesen_lot
                    ),
                )
            )

            yeni_planlar.append(
                replace(
                    varlik_plani,
                    kademe_plani=(
                        yeni_kademe_plani
                    ),
                )
            )

        if not bulundu:
            raise KeyError(
                f"Varlık planı bulunamadı: {aranan}"
            )

        return cls.yeniden_muhurle(
            replace(
                plan,
                varlik_planlari=tuple(
                    yeni_planlar
                ),
            )
        )

    @classmethod
    def yeniden_muhurle(
        cls,
        plan: TopluYatirimPlani,
    ) -> TopluYatirimPlani:
        kanit = {
            "toplu_plan_id": (
                plan.toplu_plan_id
            ),
            "toplam_butce": str(
                plan.toplam_butce
            ),
            "nakit_guvenlik_payi": str(
                plan.nakit_guvenlik_payi
            ),
            "varlik_planlari": [
                {
                    "sembol": (
                        varlik.sembol
                    ),
                    "ayrilan_butce": str(
                        varlik.ayrilan_butce
                    ),
                    "kademe_plani_sha256": (
                        varlik
                        .kademe_plani
                        .plan_sha256
                    ),
                }
                for varlik
                in plan.varlik_planlari
            ],
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return replace(
            plan,
            toplu_plan_sha256=sha256(
                kodlu
            ).hexdigest(),
        )