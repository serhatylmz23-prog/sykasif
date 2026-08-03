from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_DOWN
from hashlib import sha256
import json
from typing import Any, Iterable, Literal


IslemYonu = Literal["alim", "satim"]


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.01")
    )


@dataclass(frozen=True, slots=True)
class Kademe:
    kademe_no: int
    fiyat: Decimal
    lot: int
    planlanan_tutar: Decimal
    gerceklesti: bool = False
    gerceklesen_fiyat: Decimal | None = None
    gerceklesen_lot: int | None = None

    @property
    def etkin_fiyat(self) -> Decimal:
        return (
            self.gerceklesen_fiyat
            if self.gerceklesti
            and self.gerceklesen_fiyat is not None
            else self.fiyat
        )

    @property
    def etkin_lot(self) -> int:
        return (
            self.gerceklesen_lot
            if self.gerceklesti
            and self.gerceklesen_lot is not None
            else self.lot
        )

    @property
    def gerceklesen_tutar(self) -> Decimal:
        if not self.gerceklesti:
            return Decimal("0.00")

        return _para(
            self.etkin_fiyat
            * self.etkin_lot
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kademe_no": self.kademe_no,
            "fiyat": float(self.fiyat),
            "lot": self.lot,
            "planlanan_tutar": float(
                self.planlanan_tutar
            ),
            "gerceklesti": self.gerceklesti,
            "durum_sembolu": (
                "✓"
                if self.gerceklesti
                else "○"
            ),
            "gerceklesen_fiyat": (
                float(self.gerceklesen_fiyat)
                if self.gerceklesen_fiyat is not None
                else None
            ),
            "gerceklesen_lot": (
                self.gerceklesen_lot
            ),
            "gerceklesen_tutar": float(
                self.gerceklesen_tutar
            ),
        }


@dataclass(frozen=True, slots=True)
class KademePlani:
    plan_id: str
    sembol: str
    islem_yonu: IslemYonu
    toplam_butce: Decimal
    referans_fiyat: Decimal
    kademeler: tuple[Kademe, ...]
    aciklama: str
    plan_sha256: str

    @property
    def planlanan_lot(self) -> int:
        return sum(
            kademe.lot
            for kademe in self.kademeler
        )

    @property
    def planlanan_tutar(self) -> Decimal:
        return _para(
            sum(
                (
                    kademe.planlanan_tutar
                    for kademe in self.kademeler
                ),
                Decimal("0.00"),
            )
        )

    @property
    def gerceklesen_lot(self) -> int:
        return sum(
            kademe.etkin_lot
            for kademe in self.kademeler
            if kademe.gerceklesti
        )

    @property
    def gerceklesen_tutar(self) -> Decimal:
        return _para(
            sum(
                (
                    kademe.gerceklesen_tutar
                    for kademe in self.kademeler
                ),
                Decimal("0.00"),
            )
        )

    @property
    def ortalama_maliyet(self) -> Decimal | None:
        if self.gerceklesen_lot <= 0:
            return None

        return _para(
            self.gerceklesen_tutar
            / Decimal(
                self.gerceklesen_lot
            )
        )

    @property
    def kalan_butce(self) -> Decimal:
        if self.islem_yonu == "satim":
            return Decimal("0.00")

        return _para(
            max(
                Decimal("0.00"),
                self.toplam_butce
                - self.gerceklesen_tutar,
            )
        )

    @property
    def gerceklesme_orani(self) -> float:
        if self.planlanan_tutar <= 0:
            return 0.0

        oran = (
            self.gerceklesen_tutar
            / self.planlanan_tutar
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
    def maliyet_avantaji(self) -> float:
        ortalama = self.ortalama_maliyet

        if ortalama is None:
            return 0.0

        if self.referans_fiyat <= 0:
            return 0.0

        if self.islem_yonu == "alim":
            fark = (
                self.referans_fiyat
                - ortalama
            )
        else:
            fark = (
                ortalama
                - self.referans_fiyat
            )

        oran = (
            fark
            / self.referans_fiyat
            * Decimal("100")
        )

        return round(
            float(oran),
            3,
        )

    @property
    def basari_orani(self) -> float:
        gerceklesme_puani = (
            self.gerceklesme_orani
            * 0.70
        )

        maliyet_puani = min(
            100.0,
            max(
                0.0,
                self.maliyet_avantaji
                * 10.0,
            ),
        )

        return round(
            gerceklesme_puani
            + maliyet_puani * 0.30,
            3,
        )

    def kademe_guncelle(
        self,
        kademe_no: int,
        *,
        gerceklesti: bool,
        gerceklesen_fiyat: (
            Decimal | int | float | str | None
        ) = None,
        gerceklesen_lot: int | None = None,
    ) -> "KademePlani":
        bulunan = False
        yeni_kademeler: list[Kademe] = []

        for kademe in self.kademeler:
            if kademe.kademe_no != kademe_no:
                yeni_kademeler.append(
                    kademe
                )
                continue

            bulunan = True

            fiyat = (
                _para(gerceklesen_fiyat)
                if gerceklesen_fiyat is not None
                else kademe.fiyat
            )

            lot = (
                int(gerceklesen_lot)
                if gerceklesen_lot is not None
                else kademe.lot
            )

            if lot <= 0:
                raise ValueError(
                    "Gerçekleşen lot pozitif olmalıdır."
                )

            yeni_kademeler.append(
                replace(
                    kademe,
                    gerceklesti=bool(
                        gerceklesti
                    ),
                    gerceklesen_fiyat=(
                        fiyat
                        if gerceklesti
                        else None
                    ),
                    gerceklesen_lot=(
                        lot
                        if gerceklesti
                        else None
                    ),
                )
            )

        if not bulunan:
            raise KeyError(
                f"Kademe bulunamadı: {kademe_no}"
            )

        return KademePlaniMotoru.yeniden_muhurle(
            replace(
                self,
                kademeler=tuple(
                    yeni_kademeler
                ),
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "sembol": self.sembol,
            "islem_yonu": self.islem_yonu,
            "toplam_butce": float(
                self.toplam_butce
            ),
            "referans_fiyat": float(
                self.referans_fiyat
            ),
            "kademeler": [
                kademe.as_dict()
                for kademe in self.kademeler
            ],
            "planlanan_lot": (
                self.planlanan_lot
            ),
            "planlanan_tutar": float(
                self.planlanan_tutar
            ),
            "gerceklesen_lot": (
                self.gerceklesen_lot
            ),
            "gerceklesen_tutar": float(
                self.gerceklesen_tutar
            ),
            "ortalama_maliyet": (
                float(self.ortalama_maliyet)
                if self.ortalama_maliyet is not None
                else None
            ),
            "kalan_butce": float(
                self.kalan_butce
            ),
            "gerceklesme_orani": (
                self.gerceklesme_orani
            ),
            "maliyet_avantaji": (
                self.maliyet_avantaji
            ),
            "basari_orani": (
                self.basari_orani
            ),
            "aciklama": self.aciklama,
            "plan_sha256": (
                self.plan_sha256
            ),
        }


class KademePlaniMotoru:
    @classmethod
    def olustur(
        cls,
        *,
        plan_id: str,
        sembol: str,
        islem_yonu: IslemYonu,
        toplam_butce: Decimal | int | float | str,
        referans_fiyat: Decimal | int | float | str,
        fiyatlar: Iterable[
            Decimal | int | float | str
        ],
        dagilim_oranlari: (
            Iterable[
                Decimal | int | float | str
            ]
            | None
        ) = None,
        aciklama: str = "",
    ) -> KademePlani:
        butce = _para(
            toplam_butce
        )

        referans = _para(
            referans_fiyat
        )

        if butce <= 0:
            raise ValueError(
                "Yatırım bütçesi pozitif olmalıdır."
            )

        if referans <= 0:
            raise ValueError(
                "Referans fiyat pozitif olmalıdır."
            )

        fiyat_listesi = [
            _para(fiyat)
            for fiyat in fiyatlar
        ]

        if not fiyat_listesi:
            raise ValueError(
                "En az bir kademe fiyatı gereklidir."
            )

        if any(
            fiyat <= 0
            for fiyat in fiyat_listesi
        ):
            raise ValueError(
                "Kademe fiyatları pozitif olmalıdır."
            )

        if dagilim_oranlari is None:
            oran = (
                Decimal("100")
                / Decimal(
                    len(fiyat_listesi)
                )
            )

            oranlar = [
                oran
                for _ in fiyat_listesi
            ]
        else:
            oranlar = [
                Decimal(str(deger))
                for deger
                in dagilim_oranlari
            ]

        if len(oranlar) != len(
            fiyat_listesi
        ):
            raise ValueError(
                "Kademe fiyatı ile dağılım oranı "
                "sayısı eşit olmalıdır."
            )

        toplam_oran = sum(
            oranlar,
            Decimal("0")
        )

        if toplam_oran <= 0:
            raise ValueError(
                "Toplam dağılım oranı pozitif olmalıdır."
            )

        if toplam_oran > Decimal("100.0001"):
            raise ValueError(
                "Toplam dağılım oranı yüzde 100'ü aşamaz."
            )

        kademeler: list[Kademe] = []

        for sira, (
            fiyat,
            oran,
        ) in enumerate(
            zip(
                fiyat_listesi,
                oranlar,
                strict=True,
            ),
            start=1,
        ):
            ayrilan_tutar = _para(
                butce
                * oran
                / Decimal("100")
            )

            lot = int(
                (
                    ayrilan_tutar
                    / fiyat
                ).to_integral_value(
                    rounding=ROUND_DOWN
                )
            )

            if lot <= 0:
                raise ValueError(
                    f"{sira}. kademe için bütçe "
                    "en az bir lot almaya yetmiyor."
                )

            planlanan_tutar = _para(
                fiyat * lot
            )

            kademeler.append(
                Kademe(
                    kademe_no=sira,
                    fiyat=fiyat,
                    lot=lot,
                    planlanan_tutar=(
                        planlanan_tutar
                    ),
                )
            )

        plan = KademePlani(
            plan_id=str(
                plan_id
            ).strip(),
            sembol=str(
                sembol
            ).strip().upper(),
            islem_yonu=islem_yonu,
            toplam_butce=butce,
            referans_fiyat=referans,
            kademeler=tuple(
                kademeler
            ),
            aciklama=str(
                aciklama
            ).strip(),
            plan_sha256="",
        )

        return cls.yeniden_muhurle(
            plan
        )

    @classmethod
    def yeniden_muhurle(
        cls,
        plan: KademePlani,
    ) -> KademePlani:
        kanit = {
            "plan_id": plan.plan_id,
            "sembol": plan.sembol,
            "islem_yonu": plan.islem_yonu,
            "toplam_butce": str(
                plan.toplam_butce
            ),
            "referans_fiyat": str(
                plan.referans_fiyat
            ),
            "kademeler": [
                {
                    "kademe_no": kademe.kademe_no,
                    "fiyat": str(
                        kademe.fiyat
                    ),
                    "lot": kademe.lot,
                    "gerceklesti": (
                        kademe.gerceklesti
                    ),
                    "gerceklesen_fiyat": (
                        str(
                            kademe.gerceklesen_fiyat
                        )
                        if kademe.gerceklesen_fiyat
                        is not None
                        else None
                    ),
                    "gerceklesen_lot": (
                        kademe.gerceklesen_lot
                    ),
                }
                for kademe in plan.kademeler
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
            plan_sha256=sha256(
                kodlu
            ).hexdigest(),
        )