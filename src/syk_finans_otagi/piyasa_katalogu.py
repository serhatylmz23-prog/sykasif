from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable

from .cift_katman import (
    KullaniciKasasi,
    PiyasaEvreni,
    PiyasaEvreniKaydi,
)
from .modeller import VarlikTuru


@dataclass(frozen=True, slots=True)
class KatalogFiltresi:
    varlik_turu: VarlikTuru | None = None
    sektor: str | None = None
    arama: str | None = None
    yalniz_kasamdakiler: bool = False
    yalniz_kasamda_olmayanlar: bool = False
    yalniz_etkin: bool = True

    def __post_init__(self) -> None:
        if (
            self.yalniz_kasamdakiler
            and self.yalniz_kasamda_olmayanlar
        ):
            raise ValueError(
                "Kasamdakiler ve kasamda olmayanlar "
                "filtreleri aynı anda kullanılamaz."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "varlik_turu": (
                self.varlik_turu.value
                if self.varlik_turu is not None
                else None
            ),
            "sektor": self.sektor,
            "arama": self.arama,
            "yalniz_kasamdakiler": (
                self.yalniz_kasamdakiler
            ),
            "yalniz_kasamda_olmayanlar": (
                self.yalniz_kasamda_olmayanlar
            ),
            "yalniz_etkin": self.yalniz_etkin,
        }


@dataclass(frozen=True, slots=True)
class KatalogSonucu:
    kayitlar: tuple[PiyasaEvreniKaydi, ...]
    toplam_piyasa_varligi: int
    filtrelenmis_varlik_sayisi: int
    kasadaki_varlik_sayisi: int
    filtre: KatalogFiltresi
    katalog_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "kayitlar": [
                kayit.as_dict()
                for kayit in self.kayitlar
            ],
            "toplam_piyasa_varligi": (
                self.toplam_piyasa_varligi
            ),
            "filtrelenmis_varlik_sayisi": (
                self.filtrelenmis_varlik_sayisi
            ),
            "kasadaki_varlik_sayisi": (
                self.kasadaki_varlik_sayisi
            ),
            "filtre": self.filtre.as_dict(),
            "katalog_sha256": (
                self.katalog_sha256
            ),
        }


class PiyasaKatalogMotoru:
    @classmethod
    def filtrele(
        cls,
        *,
        piyasa: PiyasaEvreni,
        kasa: KullaniciKasasi,
        filtre: KatalogFiltresi,
    ) -> KatalogSonucu:
        tum_kayitlar = piyasa.listele(
            yalniz_etkin=filtre.yalniz_etkin
        )

        kasa_anahtarlari = kasa.semboller()

        kayitlar = list(tum_kayitlar)

        if filtre.varlik_turu is not None:
            kayitlar = [
                kayit
                for kayit in kayitlar
                if (
                    kayit.varlik_turu
                    == filtre.varlik_turu
                )
            ]

        if filtre.sektor:
            sektor = (
                str(filtre.sektor)
                .strip()
                .casefold()
            )

            kayitlar = [
                kayit
                for kayit in kayitlar
                if (
                    kayit.sektor
                    .strip()
                    .casefold()
                    == sektor
                )
            ]

        if filtre.arama:
            arama = (
                str(filtre.arama)
                .strip()
                .casefold()
            )

            kayitlar = [
                kayit
                for kayit in kayitlar
                if (
                    arama
                    in kayit.sembol.casefold()
                    or arama
                    in kayit.ad.casefold()
                    or arama
                    in kayit.sektor.casefold()
                )
            ]

        if filtre.yalniz_kasamdakiler:
            kayitlar = [
                kayit
                for kayit in kayitlar
                if (
                    kayit.sembol,
                    kayit.varlik_turu,
                )
                in kasa_anahtarlari
            ]

        if filtre.yalniz_kasamda_olmayanlar:
            kayitlar = [
                kayit
                for kayit in kayitlar
                if (
                    kayit.sembol,
                    kayit.varlik_turu,
                )
                not in kasa_anahtarlari
            ]

        kayitlar = sorted(
            kayitlar,
            key=lambda kayit: (
                kayit.varlik_turu.value,
                kayit.sektor.casefold(),
                kayit.sembol,
            ),
        )

        kanit = {
            "kayitlar": [
                kayit.as_dict()
                for kayit in kayitlar
            ],
            "toplam_piyasa_varligi": len(
                tum_kayitlar
            ),
            "filtrelenmis_varlik_sayisi": len(
                kayitlar
            ),
            "kasadaki_varlik_sayisi": len(
                kasa_anahtarlari
            ),
            "filtre": filtre.as_dict(),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return KatalogSonucu(
            kayitlar=tuple(kayitlar),
            toplam_piyasa_varligi=len(
                tum_kayitlar
            ),
            filtrelenmis_varlik_sayisi=len(
                kayitlar
            ),
            kasadaki_varlik_sayisi=len(
                kasa_anahtarlari
            ),
            filtre=filtre,
            katalog_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    @classmethod
    def kasif_aday_havuzu(
        cls,
        *,
        piyasa: PiyasaEvreni,
        kasa: KullaniciKasasi,
        varlik_turleri: Iterable[
            VarlikTuru
        ] | None = None,
    ) -> KatalogSonucu:
        izinli_turler = (
            set(varlik_turleri)
            if varlik_turleri is not None
            else None
        )

        sonuc = cls.filtrele(
            piyasa=piyasa,
            kasa=kasa,
            filtre=KatalogFiltresi(
                yalniz_kasamda_olmayanlar=True,
            ),
        )

        if izinli_turler is None:
            return sonuc

        secilenler = tuple(
            kayit
            for kayit in sonuc.kayitlar
            if kayit.varlik_turu
            in izinli_turler
        )

        kanit = {
            "kayitlar": [
                kayit.as_dict()
                for kayit in secilenler
            ],
            "toplam_piyasa_varligi": (
                sonuc.toplam_piyasa_varligi
            ),
            "filtrelenmis_varlik_sayisi": len(
                secilenler
            ),
            "kasadaki_varlik_sayisi": (
                sonuc.kasadaki_varlik_sayisi
            ),
            "filtre": sonuc.filtre.as_dict(),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return KatalogSonucu(
            kayitlar=secilenler,
            toplam_piyasa_varligi=(
                sonuc.toplam_piyasa_varligi
            ),
            filtrelenmis_varlik_sayisi=len(
                secilenler
            ),
            kasadaki_varlik_sayisi=(
                sonuc.kasadaki_varlik_sayisi
            ),
            filtre=sonuc.filtre,
            katalog_sha256=sha256(
                kodlu
            ).hexdigest(),
        )