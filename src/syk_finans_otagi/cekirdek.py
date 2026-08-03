from __future__ import annotations

from decimal import Decimal
from threading import RLock
from typing import Any, Iterable
from uuid import uuid4

from .kademe_plani import (
    KademePlani,
    KademePlaniMotoru,
)
from .modeller import (
    VarlikTuru,
    VeriGuncelligi,
    YatirimKosulu,
)
from .portfoy import Portfoy


class SyFinansOtagiCekirdegi:
    def __init__(self) -> None:
        self.portfoy = Portfoy()

        self._planlar: dict[
            str,
            KademePlani,
        ] = {}

        self._veri_durumlari: dict[
            str,
            VeriGuncelligi,
        ] = {}

        self._lock = RLock()

    def yatirim_plani_olustur(
        self,
        *,
        sembol: str,
        toplam_butce: Decimal | int | float | str,
        referans_fiyat: Decimal | int | float | str,
        fiyatlar: Iterable[
            Decimal | int | float | str
        ],
        yatirim_kosulu: YatirimKosulu,
        dagilim_oranlari: (
            Iterable[
                Decimal | int | float | str
            ]
            | None
        ) = None,
        islem_yonu: str = "alim",
    ) -> KademePlani:
        if islem_yonu not in {
            "alim",
            "satim",
        }:
            raise ValueError(
                "İşlem yönü alım veya satım olmalıdır."
            )

        plan_id = (
            f"SYF-{uuid4().hex[:20]}"
        )

        plan = KademePlaniMotoru.olustur(
            plan_id=plan_id,
            sembol=sembol,
            islem_yonu=islem_yonu,
            toplam_butce=toplam_butce,
            referans_fiyat=referans_fiyat,
            fiyatlar=fiyatlar,
            dagilim_oranlari=(
                dagilim_oranlari
            ),
            aciklama=(
                "Yatırım koşulu: "
                f"{yatirim_kosulu.value}"
            ),
        )

        with self._lock:
            self._planlar[
                plan.plan_id
            ] = plan

        return plan

    def kademe_durumu_degistir(
        self,
        plan_id: str,
        kademe_no: int,
        *,
        gerceklesti: bool,
        gerceklesen_fiyat: (
            Decimal | int | float | str | None
        ) = None,
        gerceklesen_lot: int | None = None,
    ) -> KademePlani:
        with self._lock:
            try:
                plan = self._planlar[
                    plan_id
                ]
            except KeyError as error:
                raise KeyError(
                    f"Plan bulunamadı: {plan_id}"
                ) from error

            yeni_plan = (
                plan.kademe_guncelle(
                    kademe_no,
                    gerceklesti=gerceklesti,
                    gerceklesen_fiyat=(
                        gerceklesen_fiyat
                    ),
                    gerceklesen_lot=(
                        gerceklesen_lot
                    ),
                )
            )

            self._planlar[
                plan_id
            ] = yeni_plan

            return yeni_plan

    def plan_getir(
        self,
        plan_id: str,
    ) -> KademePlani:
        with self._lock:
            try:
                return self._planlar[
                    plan_id
                ]
            except KeyError as error:
                raise KeyError(
                    f"Plan bulunamadı: {plan_id}"
                ) from error

    def portfoye_ekle(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
        miktar: Decimal | int | float | str,
        birim_fiyat: Decimal | int | float | str,
        islem_tarihi: str,
        komisyon: Decimal | int | float | str = 0,
        kaynak: str = "elle_giris",
    ) -> dict[str, Any]:
        kayit = self.portfoy.ekle(
            kayit_id=(
                f"SYF-KYT-{uuid4().hex[:18]}"
            ),
            sembol=sembol,
            varlik_turu=varlik_turu,
            miktar=miktar,
            birim_fiyat=birim_fiyat,
            islem_tarihi=islem_tarihi,
            komisyon=komisyon,
            kaynak=kaynak,
        )

        return kayit.as_dict()

    def veri_durumu_kaydet(
        self,
        sembol: str,
        veri_guncelligi: VeriGuncelligi,
    ) -> dict[str, Any]:
        anahtar = sembol.strip().upper()

        with self._lock:
            self._veri_durumlari[
                anahtar
            ] = veri_guncelligi

        return veri_guncelligi.as_dict()

    def kasa_ozeti(
        self,
        sembol: str,
    ) -> dict[str, Any]:
        anahtar = sembol.strip().upper()

        with self._lock:
            planlar = [
                plan
                for plan in self._planlar.values()
                if plan.sembol == anahtar
            ]

            veri = self._veri_durumlari.get(
                anahtar
            )

        portfoy_ozeti = self.portfoy.ozet(
            anahtar
        )

        return {
            "sembol": anahtar,
            "portfoy": portfoy_ozeti,
            "planlar": [
                plan.as_dict()
                for plan in planlar
            ],
            "veri_guncelligi": (
                veri.as_dict()
                if veri is not None
                else None
            ),
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
            "durum": "hazir",
        }