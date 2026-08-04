from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .finans_calisma_profili import (
    SyFinansCalismaProfili,
)
from .gercek_kaynak_sozlesmeleri import (
    BildirimOnemi,
)
from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001")
    )


@dataclass(frozen=True, slots=True)
class PiyasaGorunumKarti:
    sembol: str
    varlik_turu: VarlikTuru
    fiyat: Decimal
    veri_akis_durumu: VeriAkisDurumu
    kaynaklar: tuple[str, ...]
    aciklama: str
    kanit_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "fiyat": float(
                self.fiyat
            ),
            "veri_akis_durumu": (
                self.veri_akis_durumu.value
            ),
            "kaynaklar": list(
                self.kaynaklar
            ),
            "aciklama": self.aciklama,
            "kanit_sha256": (
                self.kanit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class KasaGorunumKarti:
    sembol: str
    varlik_turu: VarlikTuru
    miktar: Decimal
    ortalama_maliyet: Decimal
    guncel_fiyat: Decimal
    toplam_maliyet: Decimal
    guncel_deger: Decimal
    kar_zarar: Decimal
    kar_zarar_orani: float
    veri_akis_durumu: VeriAkisDurumu
    kanit_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "miktar": float(
                self.miktar
            ),
            "ortalama_maliyet": float(
                self.ortalama_maliyet
            ),
            "guncel_fiyat": float(
                self.guncel_fiyat
            ),
            "toplam_maliyet": float(
                self.toplam_maliyet
            ),
            "guncel_deger": float(
                self.guncel_deger
            ),
            "kar_zarar": float(
                self.kar_zarar
            ),
            "kar_zarar_orani": (
                self.kar_zarar_orani
            ),
            "veri_akis_durumu": (
                self.veri_akis_durumu.value
            ),
            "kanit_sha256": (
                self.kanit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class KaynakSaglikKarti:
    saglayici_id: str
    kaynak_sinifi: str
    durum: str
    veri_akis_durumu: str | None
    basari_orani: float
    son_hata: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "kaynak_sinifi": (
                self.kaynak_sinifi
            ),
            "durum": self.durum,
            "veri_akis_durumu": (
                self.veri_akis_durumu
            ),
            "basari_orani": (
                self.basari_orani
            ),
            "son_hata": self.son_hata,
        }


@dataclass(frozen=True, slots=True)
class KapBildirimKarti:
    bildirim_id: str
    sembol: str
    baslik: str
    yayin_zamani: str
    onem: BildirimOnemi
    kaynak_adresi: str
    ozet: str
    bildirim_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "bildirim_id": (
                self.bildirim_id
            ),
            "sembol": self.sembol,
            "baslik": self.baslik,
            "yayin_zamani": (
                self.yayin_zamani
            ),
            "onem": self.onem.value,
            "kaynak_adresi": (
                self.kaynak_adresi
            ),
            "ozet": self.ozet,
            "bildirim_sha256": (
                self.bildirim_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class ZamanSerisiNoktasi:
    zaman: str
    fiyat: Decimal
    hacim: Decimal | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "zaman": self.zaman,
            "fiyat": float(
                self.fiyat
            ),
            "hacim": (
                float(self.hacim)
                if self.hacim is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class FinansGorunumPaketi:
    uretilme_zamani: str
    piyasa_kartlari: tuple[
        PiyasaGorunumKarti,
        ...
    ]
    kasa_kartlari: tuple[
        KasaGorunumKarti,
        ...
    ]
    kaynak_saglik_kartlari: tuple[
        KaynakSaglikKarti,
        ...
    ]
    kap_bildirim_kartlari: tuple[
        KapBildirimKarti,
        ...
    ]
    paket_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "syfinans-gorunum-paketi/v1"
            ),
            "uretilme_zamani": (
                self.uretilme_zamani
            ),
            "piyasa_kartlari": [
                kart.as_dict()
                for kart in self.piyasa_kartlari
            ],
            "kasa_kartlari": [
                kart.as_dict()
                for kart in self.kasa_kartlari
            ],
            "kaynak_saglik_kartlari": [
                kart.as_dict()
                for kart
                in self.kaynak_saglik_kartlari
            ],
            "kap_bildirim_kartlari": [
                kart.as_dict()
                for kart
                in self.kap_bildirim_kartlari
            ],
            "paket_sha256": (
                self.paket_sha256
            ),
        }


class FinansGorunumMotoru:
    def __init__(
        self,
        *,
        calisma_profili: (
            SyFinansCalismaProfili
        ),
    ) -> None:
        self.calisma_profili = (
            calisma_profili
        )

    def piyasa_karti_uret(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> PiyasaGorunumKarti:
        sonuc = (
            self.calisma_profili
            .varlik_verisi_getir(
                sembol=sembol,
                varlik_turu=(
                    varlik_turu
                ),
            )
        )

        return PiyasaGorunumKarti(
            sembol=sonuc.sembol,
            varlik_turu=(
                sonuc.varlik_turu
            ),
            fiyat=_para(
                sonuc.secilen_fiyat
            ),
            veri_akis_durumu=(
                sonuc.veri_akis_durumu
            ),
            kaynaklar=(
                sonuc.kullanilan_kaynaklar
            ),
            aciklama=(
                sonuc.kullanici_aciklamasi
            ),
            kanit_sha256=(
                sonuc.merkez_sha256
            ),
        )

    def kasa_karti_uret(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
        miktar: Decimal | int | float | str,
        ortalama_maliyet: (
            Decimal | int | float | str
        ),
    ) -> KasaGorunumKarti:
        piyasa = self.piyasa_karti_uret(
            sembol=sembol,
            varlik_turu=varlik_turu,
        )

        miktar_degeri = _para(
            miktar
        )

        maliyet_degeri = _para(
            ortalama_maliyet
        )

        toplam_maliyet = _para(
            miktar_degeri
            * maliyet_degeri
        )

        guncel_deger = _para(
            miktar_degeri
            * piyasa.fiyat
        )

        kar_zarar = _para(
            guncel_deger
            - toplam_maliyet
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
            if toplam_maliyet > 0
            else 0.0
        )

        kanit = {
            "sembol": piyasa.sembol,
            "varlik_turu": (
                varlik_turu.value
            ),
            "miktar": str(
                miktar_degeri
            ),
            "ortalama_maliyet": str(
                maliyet_degeri
            ),
            "guncel_fiyat": str(
                piyasa.fiyat
            ),
            "piyasa_kanit_sha256": (
                piyasa.kanit_sha256
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return KasaGorunumKarti(
            sembol=piyasa.sembol,
            varlik_turu=varlik_turu,
            miktar=miktar_degeri,
            ortalama_maliyet=(
                maliyet_degeri
            ),
            guncel_fiyat=(
                piyasa.fiyat
            ),
            toplam_maliyet=(
                toplam_maliyet
            ),
            guncel_deger=(
                guncel_deger
            ),
            kar_zarar=kar_zarar,
            kar_zarar_orani=(
                kar_zarar_orani
            ),
            veri_akis_durumu=(
                piyasa.veri_akis_durumu
            ),
            kanit_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    def kaynak_saglik_kartlari(
        self,
    ) -> tuple[
        KaynakSaglikKarti,
        ...
    ]:
        ozet = (
            self.calisma_profili
            .kaynak_saglik_ozeti()
        )

        return tuple(
            KaynakSaglikKarti(
                saglayici_id=(
                    kaynak[
                        "saglayici_id"
                    ]
                ),
                kaynak_sinifi=(
                    kaynak[
                        "kaynak_sinifi"
                    ]
                ),
                durum=(
                    kaynak["durum"]
                ),
                veri_akis_durumu=(
                    kaynak[
                        "veri_akis_durumu"
                    ]
                ),
                basari_orani=float(
                    kaynak[
                        "basari_orani"
                    ]
                ),
                son_hata=(
                    kaynak["son_hata"]
                ),
            )
            for kaynak in ozet[
                "kaynaklar"
            ]
        )

    def kap_kartlari_uret(
        self,
        *,
        sembol: str | None = None,
        limit: int = 20,
    ) -> tuple[
        KapBildirimKarti,
        ...
    ]:
        sonuc = (
            self.calisma_profili
            .kap_bildirimleri_getir(
                sembol=sembol,
                limit=limit,
            )
        )

        onem_sirasi = {
            BildirimOnemi.KRITIK: 4,
            BildirimOnemi.ONEMLI: 3,
            BildirimOnemi.DIKKAT: 2,
            BildirimOnemi.BILGI: 1,
        }

        bildirimler = sorted(
            sonuc.bildirimler,
            key=lambda bildirim: (
                onem_sirasi[
                    bildirim.onem
                ],
                bildirim.yayin_zamani,
            ),
            reverse=True,
        )

        return tuple(
            KapBildirimKarti(
                bildirim_id=(
                    bildirim.bildirim_id
                ),
                sembol=bildirim.sembol,
                baslik=bildirim.baslik,
                yayin_zamani=(
                    bildirim.yayin_zamani
                ),
                onem=bildirim.onem,
                kaynak_adresi=(
                    bildirim.kaynak_adresi
                ),
                ozet=bildirim.ozet,
                bildirim_sha256=(
                    bildirim
                    .bildirim_sha256
                ),
            )
            for bildirim
            in bildirimler
        )

    def paket_uret(
        self,
        *,
        piyasa_varliklari: Iterable[
            tuple[str, VarlikTuru]
        ] = (),
        kasa_varliklari: Iterable[
            Mapping[str, Any]
        ] = (),
        kap_sembolu: str | None = None,
        kap_limiti: int = 20,
    ) -> FinansGorunumPaketi:
        uretilme_zamani = _simdi()

        piyasa_kartlari = tuple(
            self.piyasa_karti_uret(
                sembol=sembol,
                varlik_turu=varlik_turu,
            )
            for sembol, varlik_turu
            in piyasa_varliklari
        )

        kasa_kartlari = tuple(
            self.kasa_karti_uret(
                sembol=str(
                    kayit["sembol"]
                ),
                varlik_turu=(
                    kayit["varlik_turu"]
                ),
                miktar=kayit["miktar"],
                ortalama_maliyet=(
                    kayit[
                        "ortalama_maliyet"
                    ]
                ),
            )
            for kayit in kasa_varliklari
        )

        saglik_kartlari = (
            self.kaynak_saglik_kartlari()
        )

        try:
            kap_kartlari = (
                self.kap_kartlari_uret(
                    sembol=kap_sembolu,
                    limit=kap_limiti,
                )
            )
        except ConnectionError:
            kap_kartlari = ()

        kanit = {
            "uretilme_zamani": (
                uretilme_zamani
            ),
            "piyasa": [
                kart.kanit_sha256
                for kart
                in piyasa_kartlari
            ],
            "kasa": [
                kart.kanit_sha256
                for kart
                in kasa_kartlari
            ],
            "saglik": [
                kart.as_dict()
                for kart
                in saglik_kartlari
            ],
            "kap": [
                kart.bildirim_sha256
                for kart
                in kap_kartlari
            ],
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return FinansGorunumPaketi(
            uretilme_zamani=(
                uretilme_zamani
            ),
            piyasa_kartlari=(
                piyasa_kartlari
            ),
            kasa_kartlari=(
                kasa_kartlari
            ),
            kaynak_saglik_kartlari=(
                saglik_kartlari
            ),
            kap_bildirim_kartlari=(
                kap_kartlari
            ),
            paket_sha256=sha256(
                kodlu
            ).hexdigest(),
        )