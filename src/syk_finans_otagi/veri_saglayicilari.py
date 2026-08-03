from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Iterable

from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
    VeriGuncelligi,
)


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001")
    )


def _zaman(
    deger: str | None = None,
) -> str:
    if deger is None:
        return datetime.now(
            UTC
        ).isoformat()

    metin = str(
        deger
    ).strip()

    if not metin:
        raise ValueError(
            "Zaman damgası boş olamaz."
        )

    try:
        datetime.fromisoformat(
            metin.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError as error:
        raise ValueError(
            "Geçersiz zaman damgası: "
            f"{metin}"
        ) from error

    return metin


@dataclass(frozen=True, slots=True)
class PiyasaVerisi:
    sembol: str
    varlik_turu: VarlikTuru
    fiyat: Decimal
    para_birimi: str
    zaman_damgasi: str
    kaynak: str
    saglayici_id: str
    veri_durumu: VeriAkisDurumu
    gecikme_saniyesi: int = 0
    alis_fiyati: Decimal | None = None
    satis_fiyati: Decimal | None = None
    hacim: Decimal | None = None
    degisim_orani: float | None = None
    dogrulandi: bool = False
    veri_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.sembol.strip():
            raise ValueError(
                "Varlık sembolü boş olamaz."
            )

        if self.fiyat <= 0:
            raise ValueError(
                "Piyasa fiyatı pozitif olmalıdır."
            )

        if not self.para_birimi.strip():
            raise ValueError(
                "Para birimi boş olamaz."
            )

        if not self.kaynak.strip():
            raise ValueError(
                "Veri kaynağı boş olamaz."
            )

        if not self.saglayici_id.strip():
            raise ValueError(
                "Sağlayıcı kimliği boş olamaz."
            )

        _zaman(
            self.zaman_damgasi
        )

    @property
    def guncellik(self) -> VeriGuncelligi:
        if (
            self.veri_durumu
            == VeriAkisDurumu.ANLIK
        ):
            return VeriGuncelligi.anlik(
                kaynak=self.kaynak,
                son_guncelleme=(
                    self.zaman_damgasi
                ),
            )

        if (
            self.veri_durumu
            == VeriAkisDurumu.GECIKMELI
        ):
            return VeriGuncelligi.gecikmeli(
                kaynak=self.kaynak,
                gecikme_saniyesi=max(
                    1,
                    self.gecikme_saniyesi,
                ),
                son_guncelleme=(
                    self.zaman_damgasi
                ),
            )

        return VeriGuncelligi.cevrimdisi(
            kaynak=self.kaynak,
            son_guncelleme=(
                self.zaman_damgasi
            ),
            gecikme_saniyesi=max(
                0,
                self.gecikme_saniyesi,
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "fiyat": float(
                self.fiyat
            ),
            "para_birimi": (
                self.para_birimi
            ),
            "zaman_damgasi": (
                self.zaman_damgasi
            ),
            "kaynak": self.kaynak,
            "saglayici_id": (
                self.saglayici_id
            ),
            "veri_durumu": (
                self.veri_durumu.value
            ),
            "gecikme_saniyesi": (
                self.gecikme_saniyesi
            ),
            "alis_fiyati": (
                float(self.alis_fiyati)
                if self.alis_fiyati
                is not None
                else None
            ),
            "satis_fiyati": (
                float(self.satis_fiyati)
                if self.satis_fiyati
                is not None
                else None
            ),
            "hacim": (
                float(self.hacim)
                if self.hacim
                is not None
                else None
            ),
            "degisim_orani": (
                self.degisim_orani
            ),
            "dogrulandi": self.dogrulandi,
            "guncellik": (
                self.guncellik.as_dict()
            ),
            "veri_sha256": (
                self.veri_sha256
            ),
        }


class VeriSaglayici(ABC):
    @property
    @abstractmethod
    def saglayici_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def desteklenen_varliklar(
        self,
    ) -> tuple[VarlikTuru, ...]:
        raise NotImplementedError

    @abstractmethod
    def veri_getir(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> PiyasaVerisi:
        raise NotImplementedError

    def destekliyor(
        self,
        varlik_turu: VarlikTuru,
    ) -> bool:
        return (
            varlik_turu
            in self.desteklenen_varliklar
        )


class DenemeVeriSaglayici(
    VeriSaglayici
):
    def __init__(
        self,
        *,
        saglayici_id: str = (
            "syfinans-deneme"
        ),
        kaynak: str = (
            "SyFinansOtağı deneme verisi"
        ),
        veriler: dict[
            tuple[str, VarlikTuru],
            Decimal | int | float | str,
        ] | None = None,
        veri_durumu: (
            VeriAkisDurumu
        ) = VeriAkisDurumu.ANLIK,
        gecikme_saniyesi: int = 0,
        hata_uret: bool = False,
    ) -> None:
        self._saglayici_id = str(
            saglayici_id
        ).strip()

        self.kaynak = str(
            kaynak
        ).strip()

        self.veriler = {
            (
                str(sembol)
                .strip()
                .upper(),
                varlik_turu,
            ): _para(fiyat)
            for (
                sembol,
                varlik_turu,
            ), fiyat in (
                veriler
                or {}
            ).items()
        }

        self.veri_durumu = (
            veri_durumu
        )

        self.gecikme_saniyesi = max(
            0,
            int(
                gecikme_saniyesi
            ),
        )

        self.hata_uret = bool(
            hata_uret
        )

    @property
    def saglayici_id(self) -> str:
        return self._saglayici_id

    @property
    def desteklenen_varliklar(
        self,
    ) -> tuple[VarlikTuru, ...]:
        return tuple(
            VarlikTuru
        )

    def veri_getir(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> PiyasaVerisi:
        if self.hata_uret:
            raise ConnectionError(
                "Deneme sağlayıcısına "
                "ulaşılamadı."
            )

        anahtar = (
            str(sembol)
            .strip()
            .upper(),
            varlik_turu,
        )

        if anahtar not in self.veriler:
            raise KeyError(
                "Deneme verisi bulunamadı: "
                f"{anahtar[0]}"
            )

        veri = PiyasaVerisi(
            sembol=anahtar[0],
            varlik_turu=varlik_turu,
            fiyat=self.veriler[
                anahtar
            ],
            para_birimi="TRY",
            zaman_damgasi=_zaman(),
            kaynak=self.kaynak,
            saglayici_id=(
                self.saglayici_id
            ),
            veri_durumu=(
                self.veri_durumu
            ),
            gecikme_saniyesi=(
                self.gecikme_saniyesi
            ),
            dogrulandi=True,
        )

        return VeriDogruLamaMotoru.muhurle(
            veri
        )


class VeriDogruLamaMotoru:
    @classmethod
    def muhurle(
        cls,
        veri: PiyasaVerisi,
    ) -> PiyasaVerisi:
        kanit = {
            "sembol": veri.sembol,
            "varlik_turu": (
                veri.varlik_turu.value
            ),
            "fiyat": str(
                veri.fiyat
            ),
            "para_birimi": (
                veri.para_birimi
            ),
            "zaman_damgasi": (
                veri.zaman_damgasi
            ),
            "kaynak": veri.kaynak,
            "saglayici_id": (
                veri.saglayici_id
            ),
            "veri_durumu": (
                veri.veri_durumu.value
            ),
            "gecikme_saniyesi": (
                veri.gecikme_saniyesi
            ),
            "alis_fiyati": (
                str(veri.alis_fiyati)
                if veri.alis_fiyati
                is not None
                else None
            ),
            "satis_fiyati": (
                str(veri.satis_fiyati)
                if veri.satis_fiyati
                is not None
                else None
            ),
            "hacim": (
                str(veri.hacim)
                if veri.hacim
                is not None
                else None
            ),
            "degisim_orani": (
                veri.degisim_orani
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return replace(
            veri,
            dogrulandi=True,
            veri_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    @classmethod
    def dogrula(
        cls,
        veri: PiyasaVerisi,
    ) -> bool:
        yeniden = cls.muhurle(
            replace(
                veri,
                veri_sha256="",
            )
        )

        return (
            bool(
                veri.veri_sha256
            )
            and yeniden.veri_sha256
            == veri.veri_sha256
        )


class SonGuvenilirVeriDeposu:
    def __init__(self) -> None:
        self._veriler: dict[
            tuple[str, VarlikTuru],
            PiyasaVerisi,
        ] = {}

        self._lock = RLock()

    def kaydet(
        self,
        veri: PiyasaVerisi,
    ) -> None:
        if not (
            veri.dogrulandi
            and VeriDogruLamaMotoru
            .dogrula(veri)
        ):
            raise ValueError(
                "Doğrulanmamış piyasa verisi "
                "saklanamaz."
            )

        anahtar = (
            veri.sembol
            .strip()
            .upper(),
            veri.varlik_turu,
        )

        with self._lock:
            self._veriler[
                anahtar
            ] = veri

    def getir(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> PiyasaVerisi:
        anahtar = (
            str(sembol)
            .strip()
            .upper(),
            varlik_turu,
        )

        with self._lock:
            try:
                return self._veriler[
                    anahtar
                ]
            except KeyError as error:
                raise KeyError(
                    "Son güvenilir veri "
                    f"bulunamadı: {anahtar[0]}"
                ) from error

    def var_mi(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> bool:
        anahtar = (
            str(sembol)
            .strip()
            .upper(),
            varlik_turu,
        )

        with self._lock:
            return (
                anahtar
                in self._veriler
            )


@dataclass(frozen=True, slots=True)
class VeriGetirmeSonucu:
    veri: PiyasaVerisi
    ana_saglayici_kullanildi: bool
    son_guvenilir_veri_kullanildi: bool
    hata: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "veri": self.veri.as_dict(),
            "ana_saglayici_kullanildi": (
                self.ana_saglayici_kullanildi
            ),
            "son_guvenilir_veri_kullanildi": (
                self
                .son_guvenilir_veri_kullanildi
            ),
            "hata": self.hata,
        }


class FinansVeriKapisi:
    def __init__(
        self,
        *,
        saglayicilar: Iterable[
            VeriSaglayici
        ],
        depo: (
            SonGuvenilirVeriDeposu
            | None
        ) = None,
    ) -> None:
        self.saglayicilar = tuple(
            saglayicilar
        )

        if not self.saglayicilar:
            raise ValueError(
                "En az bir veri sağlayıcı "
                "tanımlanmalıdır."
            )

        saglayici_kimlikleri = [
            saglayici.saglayici_id
            for saglayici
            in self.saglayicilar
        ]

        if len(
            set(
                saglayici_kimlikleri
            )
        ) != len(
            saglayici_kimlikleri
        ):
            raise ValueError(
                "Aynı sağlayıcı kimliği "
                "birden fazla kullanılamaz."
            )

        self.depo = (
            depo
            or SonGuvenilirVeriDeposu()
        )

    def veri_getir(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> VeriGetirmeSonucu:
        hatalar: list[str] = []

        for saglayici in self.saglayicilar:
            if not saglayici.destekliyor(
                varlik_turu
            ):
                continue

            try:
                veri = saglayici.veri_getir(
                    sembol=sembol,
                    varlik_turu=varlik_turu,
                )

                if not (
                    veri.dogrulandi
                    and VeriDogruLamaMotoru
                    .dogrula(veri)
                ):
                    raise ValueError(
                        "Sağlayıcı doğrulanmış "
                        "veri üretmedi."
                    )

                self.depo.kaydet(
                    veri
                )

                return VeriGetirmeSonucu(
                    veri=veri,
                    ana_saglayici_kullanildi=True,
                    son_guvenilir_veri_kullanildi=False,
                    hata=None,
                )

            except (
                ConnectionError,
                TimeoutError,
                KeyError,
                ValueError,
            ) as error:
                hatalar.append(
                    f"{saglayici.saglayici_id}: "
                    f"{error}"
                )

        if self.depo.var_mi(
            sembol=sembol,
            varlik_turu=varlik_turu,
        ):
            onceki = self.depo.getir(
                sembol=sembol,
                varlik_turu=varlik_turu,
            )

            simdi = datetime.now(
                UTC
            )

            onceki_zaman = (
                datetime.fromisoformat(
                    onceki.zaman_damgasi
                    .replace(
                        "Z",
                        "+00:00",
                    )
                )
            )

            if (
                onceki_zaman.tzinfo
                is None
            ):
                onceki_zaman = (
                    onceki_zaman
                    .replace(
                        tzinfo=UTC
                    )
                )

            gecikme = max(
                0,
                int(
                    (
                        simdi
                        - onceki_zaman
                    ).total_seconds()
                ),
            )

            cevrimdisi = (
                VeriDogruLamaMotoru
                .muhurle(
                    replace(
                        onceki,
                        veri_durumu=(
                            VeriAkisDurumu
                            .CEVRIMDISI
                        ),
                        gecikme_saniyesi=(
                            gecikme
                        ),
                        dogrulandi=True,
                        veri_sha256="",
                    )
                )
            )

            return VeriGetirmeSonucu(
                veri=cevrimdisi,
                ana_saglayici_kullanildi=False,
                son_guvenilir_veri_kullanildi=True,
                hata=(
                    " · ".join(
                        hatalar
                    )
                    if hatalar
                    else (
                        "Canlı sağlayıcı "
                        "kullanılamadı."
                    )
                ),
            )

        raise ConnectionError(
            "Piyasa verisi alınamadı ve "
            "son güvenilir kayıt bulunamadı. "
            + " · ".join(
                hatalar
            )
        )