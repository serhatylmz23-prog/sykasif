from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
import json
from statistics import median
from typing import Any, Iterable

from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from .veri_saglayicilari import (
    PiyasaVerisi,
    VeriDogruLamaMotoru,
)


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001")
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


def _zaman_nesnesi(
    zaman_damgasi: str,
) -> datetime:
    sonuc = datetime.fromisoformat(
        str(
            zaman_damgasi
        ).replace(
            "Z",
            "+00:00",
        )
    )

    if sonuc.tzinfo is None:
        sonuc = sonuc.replace(
            tzinfo=UTC
        )

    return sonuc.astimezone(
        UTC
    )


class KaynakTuru(StrEnum):
    RESMI = "resmi"
    LISANSLI_PIYASA = "lisansli_piyasa"
    KURUMSAL = "kurumsal"
    BANKA = "banka"
    ARACI_KURUM = "araci_kurum"
    KAMUSAL = "kamusal"
    YEREL_KAYIT = "yerel_kayit"
    DENEME = "deneme"


class DogrulamaDurumu(StrEnum):
    DOGRULANDI = "dogrulandi"
    KISMEN_DOGRULANDI = "kismen_dogrulandi"
    UYUSMAZLIK = "uyusmazlik"
    YETERSIZ_KAYNAK = "yetersiz_kaynak"


@dataclass(frozen=True, slots=True)
class KaynakGuvenProfili:
    saglayici_id: str
    kaynak_turu: KaynakTuru
    temel_guven_puani: float
    guncellik_puani: float
    gecmis_tutarlilik_puani: float
    kesinti_dayanim_puani: float
    lisansli: bool
    resmi: bool
    aciklama: str = ""

    def __post_init__(self) -> None:
        if not self.saglayici_id.strip():
            raise ValueError(
                "Sağlayıcı kimliği boş olamaz."
            )

    @property
    def genel_guven_puani(self) -> float:
        puan = (
            _sinirla(
                self.temel_guven_puani
            )
            * 0.35
            + _sinirla(
                self.guncellik_puani
            )
            * 0.25
            + _sinirla(
                self
                .gecmis_tutarlilik_puani
            )
            * 0.25
            + _sinirla(
                self.kesinti_dayanim_puani
            )
            * 0.15
        )

        if self.resmi:
            puan += 4.0

        if self.lisansli:
            puan += 3.0

        return _sinirla(
            puan
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "kaynak_turu": (
                self.kaynak_turu.value
            ),
            "temel_guven_puani": (
                _sinirla(
                    self.temel_guven_puani
                )
            ),
            "guncellik_puani": (
                _sinirla(
                    self.guncellik_puani
                )
            ),
            "gecmis_tutarlilik_puani": (
                _sinirla(
                    self
                    .gecmis_tutarlilik_puani
                )
            ),
            "kesinti_dayanim_puani": (
                _sinirla(
                    self.kesinti_dayanim_puani
                )
            ),
            "lisansli": self.lisansli,
            "resmi": self.resmi,
            "genel_guven_puani": (
                self.genel_guven_puani
            ),
            "aciklama": self.aciklama,
        }


@dataclass(frozen=True, slots=True)
class KaynakliPiyasaVerisi:
    veri: PiyasaVerisi
    guven_profili: KaynakGuvenProfili

    def __post_init__(self) -> None:
        if (
            self.veri.saglayici_id
            != self.guven_profili.saglayici_id
        ):
            raise ValueError(
                "Piyasa verisi ile güven profili "
                "aynı sağlayıcıya ait olmalıdır."
            )

        if not (
            self.veri.dogrulandi
            and VeriDogruLamaMotoru
            .dogrula(
                self.veri
            )
        ):
            raise ValueError(
                "Çapraz doğrulamaya yalnız "
                "mühürlü veri kabul edilir."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "veri": self.veri.as_dict(),
            "guven_profili": (
                self.guven_profili
                .as_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class KaynakKarsilastirmasi:
    saglayici_id: str
    fiyat: Decimal
    uzlasma_fiyatindan_fark_orani: float
    zaman_farki_saniyesi: int
    guven_puani: float
    kabul_edildi: bool
    ret_nedeni: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "fiyat": float(
                self.fiyat
            ),
            "uzlasma_fiyatindan_fark_orani": (
                self
                .uzlasma_fiyatindan_fark_orani
            ),
            "zaman_farki_saniyesi": (
                self.zaman_farki_saniyesi
            ),
            "guven_puani": (
                self.guven_puani
            ),
            "kabul_edildi": (
                self.kabul_edildi
            ),
            "ret_nedeni": self.ret_nedeni,
        }


@dataclass(frozen=True, slots=True)
class CaprazDogrulamaSonucu:
    sembol: str
    varlik_turu: VarlikTuru
    uzlasma_fiyati: Decimal | None
    para_birimi: str | None
    dogrulama_durumu: DogrulamaDurumu
    kaynak_sayisi: int
    kabul_edilen_kaynak_sayisi: int
    reddedilen_kaynak_sayisi: int
    kaynak_guven_puani: float
    fiyat_tutarlilik_puani: float
    zaman_tutarlilik_puani: float
    toplam_kanit_puani: float
    veri_akis_durumu: VeriAkisDurumu
    karsilastirmalar: tuple[
        KaynakKarsilastirmasi,
        ...
    ]
    aciklama: str
    dogrulama_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "uzlasma_fiyati": (
                float(
                    self.uzlasma_fiyati
                )
                if self.uzlasma_fiyati
                is not None
                else None
            ),
            "para_birimi": (
                self.para_birimi
            ),
            "dogrulama_durumu": (
                self.dogrulama_durumu.value
            ),
            "kaynak_sayisi": (
                self.kaynak_sayisi
            ),
            "kabul_edilen_kaynak_sayisi": (
                self
                .kabul_edilen_kaynak_sayisi
            ),
            "reddedilen_kaynak_sayisi": (
                self
                .reddedilen_kaynak_sayisi
            ),
            "kaynak_guven_puani": (
                self.kaynak_guven_puani
            ),
            "fiyat_tutarlilik_puani": (
                self.fiyat_tutarlilik_puani
            ),
            "zaman_tutarlilik_puani": (
                self.zaman_tutarlilik_puani
            ),
            "toplam_kanit_puani": (
                self.toplam_kanit_puani
            ),
            "veri_akis_durumu": (
                self.veri_akis_durumu.value
            ),
            "karsilastirmalar": [
                kayit.as_dict()
                for kayit
                in self.karsilastirmalar
            ],
            "aciklama": self.aciklama,
            "dogrulama_sha256": (
                self.dogrulama_sha256
            ),
            "kesinlik_uyarisi": (
                "Sonuç mevcut kaynakların "
                "çapraz değerlendirmesidir; "
                "kesinlik iddiası taşımaz."
            ),
        }


class CaprazDogrulamaMotoru:
    @classmethod
    def dogrula(
        cls,
        *,
        veriler: Iterable[
            KaynakliPiyasaVerisi
        ],
        azami_fiyat_farki_orani: float = 1.0,
        azami_zaman_farki_saniyesi: int = 120,
        asgari_kaynak_guven_puani: float = 50.0,
        asgari_dogrulama_kaynagi: int = 2,
    ) -> CaprazDogrulamaSonucu:
        veri_listesi = tuple(
            veriler
        )

        if not veri_listesi:
            raise ValueError(
                "Çapraz doğrulama için "
                "en az bir veri gereklidir."
            )

        if asgari_dogrulama_kaynagi < 1:
            raise ValueError(
                "Asgari doğrulama kaynağı "
                "en az bir olmalıdır."
            )

        if azami_fiyat_farki_orani < 0:
            raise ValueError(
                "Azami fiyat farkı negatif olamaz."
            )

        if azami_zaman_farki_saniyesi < 0:
            raise ValueError(
                "Azami zaman farkı negatif olamaz."
            )

        ilk = veri_listesi[0].veri

        sembol = (
            ilk.sembol
            .strip()
            .upper()
        )

        varlik_turu = (
            ilk.varlik_turu
        )

        para_birimi = (
            ilk.para_birimi
            .strip()
            .upper()
        )

        saglayici_kimlikleri: set[str] = set()

        for kayit in veri_listesi:
            veri = kayit.veri

            if (
                veri.sembol.strip().upper()
                != sembol
            ):
                raise ValueError(
                    "Farklı sembollere ait veriler "
                    "birlikte doğrulanamaz."
                )

            if (
                veri.varlik_turu
                != varlik_turu
            ):
                raise ValueError(
                    "Farklı varlık türlerine ait "
                    "veriler birlikte doğrulanamaz."
                )

            if (
                veri.para_birimi
                .strip()
                .upper()
                != para_birimi
            ):
                raise ValueError(
                    "Farklı para birimlerindeki "
                    "veriler dönüştürülmeden "
                    "karşılaştırılamaz."
                )

            if (
                veri.saglayici_id
                in saglayici_kimlikleri
            ):
                raise ValueError(
                    "Aynı sağlayıcı birden fazla "
                    "doğrulama kaynağı olarak "
                    "kullanılamaz."
                )

            saglayici_kimlikleri.add(
                veri.saglayici_id
            )

        fiyatlar = [
            kayit.veri.fiyat
            for kayit in veri_listesi
        ]

        ham_uzlasma = _para(
            median(
                fiyatlar
            )
        )

        en_yeni_zaman = max(
            _zaman_nesnesi(
                kayit.veri.zaman_damgasi
            )
            for kayit in veri_listesi
        )

        karsilastirmalar: list[
            KaynakKarsilastirmasi
        ] = []

        kabul_edilenler: list[
            KaynakliPiyasaVerisi
        ] = []

        for kayit in veri_listesi:
            veri = kayit.veri
            guven = (
                kayit.guven_profili
                .genel_guven_puani
            )

            fark_orani = (
                abs(
                    float(
                        (
                            veri.fiyat
                            - ham_uzlasma
                        )
                        / ham_uzlasma
                        * Decimal("100")
                    )
                )
                if ham_uzlasma > 0
                else 100.0
            )

            zaman_farki = int(
                abs(
                    (
                        en_yeni_zaman
                        - _zaman_nesnesi(
                            veri.zaman_damgasi
                        )
                    ).total_seconds()
                )
            )

            ret_nedenleri: list[str] = []

            if (
                guven
                < asgari_kaynak_guven_puani
            ):
                ret_nedenleri.append(
                    "Kaynak güven puanı yetersiz."
                )

            if (
                fark_orani
                > azami_fiyat_farki_orani
            ):
                ret_nedenleri.append(
                    "Fiyat farkı izin verilen "
                    "sınırı aşıyor."
                )

            if (
                zaman_farki
                > azami_zaman_farki_saniyesi
            ):
                ret_nedenleri.append(
                    "Veri zaman farkı izin verilen "
                    "sınırı aşıyor."
                )

            kabul = not ret_nedenleri

            if kabul:
                kabul_edilenler.append(
                    kayit
                )

            karsilastirmalar.append(
                KaynakKarsilastirmasi(
                    saglayici_id=(
                        veri.saglayici_id
                    ),
                    fiyat=veri.fiyat,
                    uzlasma_fiyatindan_fark_orani=(
                        round(
                            fark_orani,
                            4,
                        )
                    ),
                    zaman_farki_saniyesi=(
                        zaman_farki
                    ),
                    guven_puani=guven,
                    kabul_edildi=kabul,
                    ret_nedeni=(
                        " ".join(
                            ret_nedenleri
                        )
                        if ret_nedenleri
                        else None
                    ),
                )
            )

        if kabul_edilenler:
            agirlikli_toplam = Decimal(
                "0"
            )

            toplam_agirlik = Decimal(
                "0"
            )

            for kayit in kabul_edilenler:
                agirlik = Decimal(
                    str(
                        kayit.guven_profili
                        .genel_guven_puani
                    )
                )

                agirlikli_toplam += (
                    kayit.veri.fiyat
                    * agirlik
                )

                toplam_agirlik += agirlik

            uzlasma_fiyati = _para(
                agirlikli_toplam
                / toplam_agirlik
            )
        else:
            uzlasma_fiyati = None

        kaynak_guven_puani = (
            round(
                sum(
                    kayit.guven_profili
                    .genel_guven_puani
                    for kayit
                    in kabul_edilenler
                )
                / len(
                    kabul_edilenler
                ),
                3,
            )
            if kabul_edilenler
            else 0.0
        )

        kabul_farklari = [
            karsilastirma
            .uzlasma_fiyatindan_fark_orani
            for karsilastirma
            in karsilastirmalar
            if karsilastirma.kabul_edildi
        ]

        fiyat_tutarlilik_puani = (
            _sinirla(
                100.0
                - (
                    sum(
                        kabul_farklari
                    )
                    / len(
                        kabul_farklari
                    )
                    * 30.0
                )
            )
            if kabul_farklari
            else 0.0
        )

        kabul_zaman_farklari = [
            karsilastirma
            .zaman_farki_saniyesi
            for karsilastirma
            in karsilastirmalar
            if karsilastirma.kabul_edildi
        ]

        zaman_tutarlilik_puani = (
            _sinirla(
                100.0
                - (
                    sum(
                        kabul_zaman_farklari
                    )
                    / len(
                        kabul_zaman_farklari
                    )
                    / max(
                        1,
                        azami_zaman_farki_saniyesi,
                    )
                    * 100.0
                )
            )
            if kabul_zaman_farklari
            else 0.0
        )

        kaynak_kapsama_puani = _sinirla(
            len(
                kabul_edilenler
            )
            / max(
                asgari_dogrulama_kaynagi,
                1,
            )
            * 100.0
        )

        toplam_kanit_puani = _sinirla(
            kaynak_guven_puani
            * 0.40
            + fiyat_tutarlilik_puani
            * 0.30
            + zaman_tutarlilik_puani
            * 0.15
            + kaynak_kapsama_puani
            * 0.15
        )

        kabul_sayisi = len(
            kabul_edilenler
        )

        if (
            kabul_sayisi
            >= asgari_dogrulama_kaynagi
            and toplam_kanit_puani >= 75
        ):
            durum = (
                DogrulamaDurumu
                .DOGRULANDI
            )

        elif kabul_sayisi >= 1:
            durum = (
                DogrulamaDurumu
                .KISMEN_DOGRULANDI
            )

        elif len(
            veri_listesi
        ) < asgari_dogrulama_kaynagi:
            durum = (
                DogrulamaDurumu
                .YETERSIZ_KAYNAK
            )

        else:
            durum = (
                DogrulamaDurumu
                .UYUSMAZLIK
            )

        akis_durumlari = {
            kayit.veri.veri_durumu
            for kayit in kabul_edilenler
        }

        if (
            VeriAkisDurumu.CEVRIMDISI
            in akis_durumlari
        ):
            akis_durumu = (
                VeriAkisDurumu
                .CEVRIMDISI
            )

        elif (
            VeriAkisDurumu.GECIKMELI
            in akis_durumlari
        ):
            akis_durumu = (
                VeriAkisDurumu
                .GECIKMELI
            )

        else:
            akis_durumu = (
                VeriAkisDurumu.ANLIK
            )

        if durum == DogrulamaDurumu.DOGRULANDI:
            aciklama = (
                "Veri birden fazla güvenilir "
                "kaynak tarafından doğrulandı."
            )

        elif (
            durum
            == DogrulamaDurumu
            .KISMEN_DOGRULANDI
        ):
            aciklama = (
                "Verinin bir bölümü doğrulandı; "
                "karar öncesinde ek kaynak "
                "beklenmelidir."
            )

        elif (
            durum
            == DogrulamaDurumu
            .YETERSIZ_KAYNAK
        ):
            aciklama = (
                "Doğrulama için yeterli sayıda "
                "bağımsız kaynak bulunmuyor."
            )

        else:
            aciklama = (
                "Kaynaklar arasında kabul edilen "
                "sınırların üzerinde uyuşmazlık var."
            )

        kanit = {
            "sembol": sembol,
            "varlik_turu": (
                varlik_turu.value
            ),
            "uzlasma_fiyati": (
                str(
                    uzlasma_fiyati
                )
                if uzlasma_fiyati
                is not None
                else None
            ),
            "para_birimi": para_birimi,
            "dogrulama_durumu": (
                durum.value
            ),
            "kaynak_guven_puani": (
                kaynak_guven_puani
            ),
            "fiyat_tutarlilik_puani": (
                fiyat_tutarlilik_puani
            ),
            "zaman_tutarlilik_puani": (
                zaman_tutarlilik_puani
            ),
            "toplam_kanit_puani": (
                toplam_kanit_puani
            ),
            "veri_akis_durumu": (
                akis_durumu.value
            ),
            "karsilastirmalar": [
                kayit.as_dict()
                for kayit
                in karsilastirmalar
            ],
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return CaprazDogrulamaSonucu(
            sembol=sembol,
            varlik_turu=varlik_turu,
            uzlasma_fiyati=(
                uzlasma_fiyati
            ),
            para_birimi=para_birimi,
            dogrulama_durumu=durum,
            kaynak_sayisi=len(
                veri_listesi
            ),
            kabul_edilen_kaynak_sayisi=(
                kabul_sayisi
            ),
            reddedilen_kaynak_sayisi=(
                len(
                    veri_listesi
                )
                - kabul_sayisi
            ),
            kaynak_guven_puani=(
                kaynak_guven_puani
            ),
            fiyat_tutarlilik_puani=(
                fiyat_tutarlilik_puani
            ),
            zaman_tutarlilik_puani=(
                zaman_tutarlilik_puani
            ),
            toplam_kanit_puani=(
                toplam_kanit_puani
            ),
            veri_akis_durumu=(
                akis_durumu
            ),
            karsilastirmalar=tuple(
                karsilastirmalar
            ),
            aciklama=aciklama,
            dogrulama_sha256=sha256(
                kodlu
            ).hexdigest(),
        )