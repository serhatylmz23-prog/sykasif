from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Iterable

from .modeller import (
    VarlikTuru,
)
from .portfoy import (
    Portfoy,
    PortfoyKaydi,
)
from .veri_saglayicilari import (
    FinansVeriKapisi,
    PiyasaVerisi,
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
class PiyasaEvreniKaydi:
    sembol: str
    varlik_turu: VarlikTuru
    ad: str
    sektor: str
    etkin: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "ad": self.ad,
            "sektor": self.sektor,
            "etkin": self.etkin,
        }


class PiyasaEvreni:
    def __init__(
        self,
        *,
        veri_kapisi: (
            FinansVeriKapisi | None
        ) = None,
    ) -> None:
        self.veri_kapisi = veri_kapisi

        self._kayitlar: dict[
            tuple[str, VarlikTuru],
            PiyasaEvreniKaydi,
        ] = {}

        self._lock = RLock()

    def varlik_ekle(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
        ad: str,
        sektor: str = "",
        etkin: bool = True,
    ) -> PiyasaEvreniKaydi:
        anahtar = (
            str(sembol)
            .strip()
            .upper(),
            varlik_turu,
        )

        if not anahtar[0]:
            raise ValueError(
                "Piyasa varlığı sembolü "
                "boş olamaz."
            )

        ad_degeri = str(
            ad
        ).strip()

        if not ad_degeri:
            raise ValueError(
                "Piyasa varlığı adı "
                "boş olamaz."
            )

        kayit = PiyasaEvreniKaydi(
            sembol=anahtar[0],
            varlik_turu=varlik_turu,
            ad=ad_degeri,
            sektor=str(
                sektor
            ).strip(),
            etkin=bool(
                etkin
            ),
        )

        with self._lock:
            self._kayitlar[
                anahtar
            ] = kayit

        return kayit

    def listele(
        self,
        *,
        varlik_turu: (
            VarlikTuru | None
        ) = None,
        yalniz_etkin: bool = True,
    ) -> list[PiyasaEvreniKaydi]:
        with self._lock:
            kayitlar = list(
                self._kayitlar.values()
            )

        if varlik_turu is not None:
            kayitlar = [
                kayit
                for kayit in kayitlar
                if (
                    kayit.varlik_turu
                    == varlik_turu
                )
            ]

        if yalniz_etkin:
            kayitlar = [
                kayit
                for kayit in kayitlar
                if kayit.etkin
            ]

        return sorted(
            kayitlar,
            key=lambda kayit: (
                kayit.varlik_turu.value,
                kayit.sembol,
            ),
        )

    def fiyat_getir(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> PiyasaVerisi:
        if self.veri_kapisi is None:
            raise RuntimeError(
                "Piyasa veri kapısı "
                "tanımlanmadı."
            )

        sonuc = (
            self.veri_kapisi
            .veri_getir(
                sembol=sembol,
                varlik_turu=varlik_turu,
            )
        )

        return sonuc.veri

    def snapshot(self) -> dict[str, Any]:
        kayitlar = self.listele(
            yalniz_etkin=False
        )

        kanit = {
            "katman": "piyasa_evreni",
            "kayitlar": [
                kayit.as_dict()
                for kayit in kayitlar
            ],
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return {
            **kanit,
            "kayit_sayisi": len(
                kayitlar
            ),
            "sha256": sha256(
                kodlu
            ).hexdigest(),
        }


@dataclass(frozen=True, slots=True)
class KasaVarlikOzeti:
    sembol: str
    varlik_turu: VarlikTuru
    toplam_miktar: Decimal
    toplam_maliyet: Decimal
    ortalama_maliyet: (
        Decimal | None
    )
    guncel_fiyat: Decimal | None
    guncel_deger: Decimal | None
    kar_zarar: Decimal | None
    kar_zarar_orani: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "toplam_miktar": float(
                self.toplam_miktar
            ),
            "toplam_maliyet": float(
                self.toplam_maliyet
            ),
            "ortalama_maliyet": (
                float(
                    self.ortalama_maliyet
                )
                if self.ortalama_maliyet
                is not None
                else None
            ),
            "guncel_fiyat": (
                float(self.guncel_fiyat)
                if self.guncel_fiyat
                is not None
                else None
            ),
            "guncel_deger": (
                float(self.guncel_deger)
                if self.guncel_deger
                is not None
                else None
            ),
            "kar_zarar": (
                float(self.kar_zarar)
                if self.kar_zarar
                is not None
                else None
            ),
            "kar_zarar_orani": (
                self.kar_zarar_orani
            ),
        }


class KullaniciKasasi:
    def __init__(
        self,
        *,
        portfoy: Portfoy | None = None,
    ) -> None:
        self.portfoy = (
            portfoy
            or Portfoy()
        )

    def kayit_ekle(
        self,
        *,
        kayit_id: str,
        sembol: str,
        varlik_turu: VarlikTuru,
        miktar: Decimal | int | float | str,
        birim_fiyat: Decimal | int | float | str,
        islem_tarihi: str,
        komisyon: Decimal | int | float | str = 0,
        kaynak: str = "elle_giris",
    ) -> PortfoyKaydi:
        return self.portfoy.ekle(
            kayit_id=kayit_id,
            sembol=sembol,
            varlik_turu=varlik_turu,
            miktar=miktar,
            birim_fiyat=birim_fiyat,
            islem_tarihi=islem_tarihi,
            komisyon=komisyon,
            kaynak=kaynak,
        )

    def varlik_ozeti(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
        guncel_fiyat: (
            Decimal | int | float | str | None
        ) = None,
    ) -> KasaVarlikOzeti:
        kayitlar = [
            kayit
            for kayit
            in self.portfoy.listele(
                sembol=sembol
            )
            if (
                kayit.varlik_turu
                == varlik_turu
            )
        ]

        toplam_miktar = sum(
            (
                kayit.miktar
                for kayit in kayitlar
            ),
            Decimal("0"),
        )

        toplam_maliyet = _para(
            sum(
                (
                    kayit.toplam_tutar
                    for kayit in kayitlar
                ),
                Decimal("0.00"),
            )
        )

        ortalama = (
            _para(
                toplam_maliyet
                / toplam_miktar
            )
            if toplam_miktar > 0
            else None
        )

        fiyat = (
            _para(guncel_fiyat)
            if guncel_fiyat is not None
            else None
        )

        guncel_deger = (
            _para(
                toplam_miktar
                * fiyat
            )
            if (
                fiyat is not None
                and toplam_miktar > 0
            )
            else None
        )

        kar_zarar = (
            _para(
                guncel_deger
                - toplam_maliyet
            )
            if guncel_deger is not None
            else None
        )

        kar_zarar_orani = (
            round(
                float(
                    kar_zarar
                    / toplam_maliyet
                    * Decimal("100")
                ),
                3,
            )
            if (
                kar_zarar is not None
                and toplam_maliyet > 0
            )
            else None
        )

        return KasaVarlikOzeti(
            sembol=(
                sembol.strip().upper()
            ),
            varlik_turu=varlik_turu,
            toplam_miktar=(
                toplam_miktar
            ),
            toplam_maliyet=(
                toplam_maliyet
            ),
            ortalama_maliyet=ortalama,
            guncel_fiyat=fiyat,
            guncel_deger=guncel_deger,
            kar_zarar=kar_zarar,
            kar_zarar_orani=(
                kar_zarar_orani
            ),
        )

    def semboller(
        self,
    ) -> set[
        tuple[str, VarlikTuru]
    ]:
        return {
            (
                kayit.sembol,
                kayit.varlik_turu,
            )
            for kayit
            in self.portfoy.listele()
        }

    def snapshot(self) -> dict[str, Any]:
        kayitlar = [
            kayit.as_dict()
            for kayit
            in self.portfoy.listele()
        ]

        kanit = {
            "katman": "kullanici_kasasi",
            "kayitlar": kayitlar,
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return {
            **kanit,
            "kayit_sayisi": len(
                kayitlar
            ),
            "sha256": sha256(
                kodlu
            ).hexdigest(),
        }


@dataclass(frozen=True, slots=True)
class CiftKatmanDegerlendirmesi:
    piyasa_varlik_sayisi: int
    kasa_varlik_sayisi: int
    piyasada_olup_kasada_olmayanlar: tuple[
        str,
        ...
    ]
    kasada_olanlar: tuple[
        str,
        ...
    ]
    degerlendirme_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "piyasa_varlik_sayisi": (
                self.piyasa_varlik_sayisi
            ),
            "kasa_varlik_sayisi": (
                self.kasa_varlik_sayisi
            ),
            "piyasada_olup_kasada_olmayanlar": (
                list(
                    self
                    .piyasada_olup_kasada_olmayanlar
                )
            ),
            "kasada_olanlar": list(
                self.kasada_olanlar
            ),
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
            "degerlendirme_sha256": (
                self.degerlendirme_sha256
            ),
        }


class SyFinansCiftKatman:
    def __init__(
        self,
        *,
        piyasa: PiyasaEvreni,
        kasa: KullaniciKasasi,
    ) -> None:
        self.piyasa = piyasa
        self.kasa = kasa

    def karsilastir(
        self,
    ) -> CiftKatmanDegerlendirmesi:
        piyasa_kayitlari = (
            self.piyasa.listele()
        )

        kasa_anahtarlari = (
            self.kasa.semboller()
        )

        piyasada_olmayan = sorted(
            {
                kayit.sembol
                for kayit
                in piyasa_kayitlari
                if (
                    kayit.sembol,
                    kayit.varlik_turu,
                )
                not in kasa_anahtarlari
            }
        )

        kasada_olan = sorted(
            {
                sembol
                for sembol, _
                in kasa_anahtarlari
            }
        )

        kanit = {
            "piyasa_varlik_sayisi": (
                len(
                    piyasa_kayitlari
                )
            ),
            "kasa_varlik_sayisi": (
                len(
                    kasa_anahtarlari
                )
            ),
            "piyasada_olup_kasada_olmayanlar": (
                piyasada_olmayan
            ),
            "kasada_olanlar": (
                kasada_olan
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return CiftKatmanDegerlendirmesi(
            piyasa_varlik_sayisi=(
                kanit[
                    "piyasa_varlik_sayisi"
                ]
            ),
            kasa_varlik_sayisi=(
                kanit[
                    "kasa_varlik_sayisi"
                ]
            ),
            piyasada_olup_kasada_olmayanlar=(
                tuple(
                    piyasada_olmayan
                )
            ),
            kasada_olanlar=tuple(
                kasada_olan
            ),
            degerlendirme_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    def ekran_sozlesmesi(
        self,
    ) -> dict[str, Any]:
        return {
            "katmanlar": [
                {
                    "katman_id": (
                        "piyasa_evreni"
                    ),
                    "baslik": (
                        "Piyasa"
                    ),
                    "aciklama": (
                        "Tüm BIST, fon, döviz "
                        "ve kıymetli madenler."
                    ),
                },
                {
                    "katman_id": (
                        "kullanici_kasasi"
                    ),
                    "baslik": (
                        "Kasam"
                    ),
                    "aciklama": (
                        "Kullanıcının sahip olduğu "
                        "varlıklar ve maliyetleri."
                    ),
                },
            ],
            "varsayilan_katman": (
                "piyasa_evreni"
            ),
            "katmanlar_karismaz": True,
            "karsilastirma_mevcut": True,
        }