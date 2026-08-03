from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .modeller import VarlikTuru


def _ondalik(
    deger: Decimal | int | float | str,
    *,
    basamak: str = "0.0001",
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal(basamak),
        rounding=ROUND_HALF_UP,
    )


def _muhur(
    veri: Mapping[str, Any],
) -> str:
    kodlu = json.dumps(
        dict(veri),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return sha256(
        kodlu
    ).hexdigest()


class YatirimSecimTuru(StrEnum):
    SERBEST = "serbest"
    KULLANICI_SECIMI = "kullanici_secimi"


class KademeTuru(StrEnum):
    ALIM = "alim"
    SATIM = "satim"


class KararYonelimi(StrEnum):
    GUCLU_ADAY = "guclu_aday"
    IZLE = "izle"
    TEMKINLI = "temkinli"
    UZAK_DUR = "uzak_dur"


@dataclass(frozen=True, slots=True)
class VarlikAdayi:
    sembol: str
    varlik_turu: VarlikTuru
    guncel_fiyat: Decimal
    guven_puani: float
    kanit_gucu: float
    risk_puani: float
    piyasa_davranis_puani: float
    kap_etki_puani: float = 50.0
    trend_puani: float = 50.0
    kullanici_secimi: bool = False

    def __post_init__(self) -> None:
        if not self.sembol.strip():
            raise ValueError(
                "Aday sembolü boş olamaz."
            )

        if self.guncel_fiyat <= 0:
            raise ValueError(
                "Güncel fiyat pozitif olmalıdır."
            )

        for ad, puan in (
            ("güven", self.guven_puani),
            ("kanıt", self.kanit_gucu),
            ("risk", self.risk_puani),
            (
                "piyasa davranışı",
                self.piyasa_davranis_puani,
            ),
            ("KAP etkisi", self.kap_etki_puani),
            ("trend", self.trend_puani),
        ):
            if not 0 <= float(puan) <= 100:
                raise ValueError(
                    f"{ad} puanı 0–100 arasında olmalıdır."
                )

    @property
    def karar_puani(self) -> float:
        puan = (
            self.guven_puani * 0.25
            + self.kanit_gucu * 0.20
            + (
                100.0 - self.risk_puani
            ) * 0.20
            + self.piyasa_davranis_puani
            * 0.15
            + self.kap_etki_puani * 0.10
            + self.trend_puani * 0.10
        )

        return round(
            max(
                0.0,
                min(
                    100.0,
                    puan,
                ),
            ),
            3,
        )

    @property
    def yonelim(self) -> KararYonelimi:
        if self.karar_puani >= 80:
            return KararYonelimi.GUCLU_ADAY

        if self.karar_puani >= 65:
            return KararYonelimi.IZLE

        if self.karar_puani >= 50:
            return KararYonelimi.TEMKINLI

        return KararYonelimi.UZAK_DUR

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol.upper(),
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "guncel_fiyat": float(
                self.guncel_fiyat
            ),
            "guven_puani": self.guven_puani,
            "kanit_gucu": self.kanit_gucu,
            "risk_puani": self.risk_puani,
            "piyasa_davranis_puani": (
                self.piyasa_davranis_puani
            ),
            "kap_etki_puani": (
                self.kap_etki_puani
            ),
            "trend_puani": self.trend_puani,
            "kullanici_secimi": (
                self.kullanici_secimi
            ),
            "karar_puani": (
                self.karar_puani
            ),
            "yonelim": self.yonelim.value,
        }


@dataclass(frozen=True, slots=True)
class ButceDagilimKaydi:
    sembol: str
    varlik_turu: VarlikTuru
    karar_puani: float
    agirlik_orani: float
    ayrilan_butce: Decimal
    tahmini_adet: Decimal
    kullanilmayan_tutar: Decimal

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "karar_puani": (
                self.karar_puani
            ),
            "agirlik_orani": (
                self.agirlik_orani
            ),
            "ayrilan_butce": float(
                self.ayrilan_butce
            ),
            "tahmini_adet": float(
                self.tahmini_adet
            ),
            "kullanilmayan_tutar": float(
                self.kullanilmayan_tutar
            ),
        }


@dataclass(frozen=True, slots=True)
class ButceDagilimPlani:
    toplam_butce: Decimal
    secim_turu: YatirimSecimTuru
    kayitlar: tuple[
        ButceDagilimKaydi,
        ...
    ]
    dagitilan_butce: Decimal
    kalan_butce: Decimal
    plan_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "syfinans-butce-dagilimi/v1"
            ),
            "toplam_butce": float(
                self.toplam_butce
            ),
            "secim_turu": (
                self.secim_turu.value
            ),
            "kayitlar": [
                kayit.as_dict()
                for kayit in self.kayitlar
            ],
            "dagitilan_butce": float(
                self.dagitilan_butce
            ),
            "kalan_butce": float(
                self.kalan_butce
            ),
            "plan_sha256": (
                self.plan_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class KademeKaydi:
    sira: int
    fiyat: Decimal
    ayrilan_tutar: Decimal
    adet: Decimal
    gerceklesti: bool = False

    @property
    def gerceklesen_tutar(self) -> Decimal:
        if not self.gerceklesti:
            return Decimal("0.0000")

        return _ondalik(
            self.fiyat * self.adet
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "sira": self.sira,
            "fiyat": float(
                self.fiyat
            ),
            "ayrilan_tutar": float(
                self.ayrilan_tutar
            ),
            "adet": float(
                self.adet
            ),
            "gerceklesti": (
                self.gerceklesti
            ),
            "gerceklesen_tutar": float(
                self.gerceklesen_tutar
            ),
        }


@dataclass(frozen=True, slots=True)
class KademePlani:
    plan_id: str
    sembol: str
    kademe_turu: KademeTuru
    toplam_butce: Decimal
    kademeler: tuple[
        KademeKaydi,
        ...
    ]
    gerceklesen_adet: Decimal
    gerceklesen_tutar: Decimal
    ortalama_maliyet: Decimal | None
    gerceklesme_orani: float
    basari_orani: float
    plan_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "syfinans-kademe-plani/v1"
            ),
            "plan_id": self.plan_id,
            "sembol": self.sembol,
            "kademe_turu": (
                self.kademe_turu.value
            ),
            "toplam_butce": float(
                self.toplam_butce
            ),
            "kademeler": [
                kademe.as_dict()
                for kademe in self.kademeler
            ],
            "gerceklesen_adet": float(
                self.gerceklesen_adet
            ),
            "gerceklesen_tutar": float(
                self.gerceklesen_tutar
            ),
            "ortalama_maliyet": (
                float(self.ortalama_maliyet)
                if self.ortalama_maliyet
                is not None
                else None
            ),
            "gerceklesme_orani": (
                self.gerceklesme_orani
            ),
            "basari_orani": (
                self.basari_orani
            ),
            "plan_sha256": (
                self.plan_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class KasifFinansYorumu:
    sembol: str
    karar_puani: float
    yonelim: KararYonelimi
    kisa_yorum: str
    kanit_ozeti: tuple[str, ...]
    risk_uyarisi: str
    kesinlik_uyarisi: str
    yorum_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "syfinans-kasif-yorumu/v1"
            ),
            "sembol": self.sembol,
            "karar_puani": (
                self.karar_puani
            ),
            "yonelim": self.yonelim.value,
            "kisa_yorum": self.kisa_yorum,
            "kanit_ozeti": list(
                self.kanit_ozeti
            ),
            "risk_uyarisi": (
                self.risk_uyarisi
            ),
            "kesinlik_uyarisi": (
                self.kesinlik_uyarisi
            ),
            "yorum_sha256": (
                self.yorum_sha256
            ),
        }


class SyFinansKararDestekMotoru:
    def adaylari_sirala(
        self,
        *,
        adaylar: Iterable[VarlikAdayi],
        secim_turu: YatirimSecimTuru,
        en_fazla_aday: int = 7,
    ) -> tuple[VarlikAdayi, ...]:
        if not 1 <= int(en_fazla_aday) <= 7:
            raise ValueError(
                "Aday sayısı 1–7 arasında olmalıdır."
            )

        liste = tuple(
            adaylar
        )

        if secim_turu == (
            YatirimSecimTuru
            .KULLANICI_SECIMI
        ):
            liste = tuple(
                aday
                for aday in liste
                if aday.kullanici_secimi
            )

        sirali = sorted(
            liste,
            key=lambda aday: (
                aday.karar_puani,
                aday.guven_puani,
                -aday.risk_puani,
                aday.sembol,
            ),
            reverse=True,
        )

        return tuple(
            sirali[
                :int(en_fazla_aday)
            ]
        )

    def butce_dagit(
        self,
        *,
        toplam_butce: (
            Decimal | int | float | str
        ),
        adaylar: Iterable[VarlikAdayi],
        secim_turu: YatirimSecimTuru,
        en_fazla_aday: int = 7,
    ) -> ButceDagilimPlani:
        butce = _ondalik(
            toplam_butce
        )

        if butce <= 0:
            raise ValueError(
                "Toplam bütçe pozitif olmalıdır."
            )

        secilenler = self.adaylari_sirala(
            adaylar=adaylar,
            secim_turu=secim_turu,
            en_fazla_aday=en_fazla_aday,
        )

        if not secilenler:
            raise ValueError(
                "Bütçe dağıtılacak aday bulunamadı."
            )

        toplam_puan = sum(
            Decimal(
                str(aday.karar_puani)
            )
            for aday in secilenler
        )

        kayitlar: list[
            ButceDagilimKaydi
        ] = []

        for aday in secilenler:
            agirlik = (
                Decimal(
                    str(aday.karar_puani)
                )
                / toplam_puan
            )

            ayrilan = _ondalik(
                butce * agirlik
            )

            adet = (
                ayrilan
                / aday.guncel_fiyat
            ).quantize(
                Decimal("1"),
                rounding=ROUND_DOWN,
            )

            kullanilan = _ondalik(
                adet
                * aday.guncel_fiyat
            )

            kullanilmayan = _ondalik(
                ayrilan - kullanilan
            )

            kayitlar.append(
                ButceDagilimKaydi(
                    sembol=(
                        aday.sembol.upper()
                    ),
                    varlik_turu=(
                        aday.varlik_turu
                    ),
                    karar_puani=(
                        aday.karar_puani
                    ),
                    agirlik_orani=round(
                        float(
                            agirlik
                            * Decimal("100")
                        ),
                        3,
                    ),
                    ayrilan_butce=ayrilan,
                    tahmini_adet=adet,
                    kullanilmayan_tutar=(
                        kullanilmayan
                    ),
                )
            )

        dagitilan = _ondalik(
            sum(
                (
                    kayit.ayrilan_butce
                    for kayit in kayitlar
                ),
                Decimal("0"),
            )
        )

        kalan = _ondalik(
            butce - dagitilan
        )

        kanit = {
            "toplam_butce": str(
                butce
            ),
            "secim_turu": (
                secim_turu.value
            ),
            "kayitlar": [
                kayit.as_dict()
                for kayit in kayitlar
            ],
        }

        return ButceDagilimPlani(
            toplam_butce=butce,
            secim_turu=secim_turu,
            kayitlar=tuple(
                kayitlar
            ),
            dagitilan_butce=(
                dagitilan
            ),
            kalan_butce=kalan,
            plan_sha256=_muhur(
                kanit
            ),
        )

    def kademe_plani_olustur(
        self,
        *,
        plan_id: str,
        sembol: str,
        kademe_turu: KademeTuru,
        fiyatlar: Iterable[
            Decimal | int | float | str
        ],
        toplam_butce: (
            Decimal | int | float | str
        ),
        gerceklesen_siralar: (
            Iterable[int]
        ) = (),
    ) -> KademePlani:
        butce = _ondalik(
            toplam_butce
        )

        fiyat_listesi = tuple(
            _ondalik(
                fiyat
            )
            for fiyat in fiyatlar
        )

        if not plan_id.strip():
            raise ValueError(
                "Plan kimliği boş olamaz."
            )

        if not sembol.strip():
            raise ValueError(
                "Sembol boş olamaz."
            )

        if butce <= 0:
            raise ValueError(
                "Toplam bütçe pozitif olmalıdır."
            )

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

        gerceklesenler = {
            int(sira)
            for sira in gerceklesen_siralar
        }

        kademe_butcesi = _ondalik(
            butce
            / Decimal(
                len(fiyat_listesi)
            )
        )

        kademeler: list[
            KademeKaydi
        ] = []

        for sira, fiyat in enumerate(
            fiyat_listesi,
            start=1,
        ):
            adet = (
                kademe_butcesi
                / fiyat
            ).quantize(
                Decimal("1"),
                rounding=ROUND_DOWN,
            )

            kademeler.append(
                KademeKaydi(
                    sira=sira,
                    fiyat=fiyat,
                    ayrilan_tutar=(
                        kademe_butcesi
                    ),
                    adet=adet,
                    gerceklesti=(
                        sira
                        in gerceklesenler
                    ),
                )
            )

        gerceklesen_kademeler = tuple(
            kademe
            for kademe in kademeler
            if kademe.gerceklesti
        )

        gerceklesen_adet = _ondalik(
            sum(
                (
                    kademe.adet
                    for kademe
                    in gerceklesen_kademeler
                ),
                Decimal("0"),
            )
        )

        gerceklesen_tutar = _ondalik(
            sum(
                (
                    kademe
                    .gerceklesen_tutar
                    for kademe
                    in gerceklesen_kademeler
                ),
                Decimal("0"),
            )
        )

        ortalama_maliyet = (
            _ondalik(
                gerceklesen_tutar
                / gerceklesen_adet
            )
            if gerceklesen_adet > 0
            else None
        )

        gerceklesme_orani = round(
            (
                len(
                    gerceklesen_kademeler
                )
                / len(kademeler)
                * 100.0
            ),
            3,
        )

        ayrilan_toplam = _ondalik(
            sum(
                (
                    kademe.ayrilan_tutar
                    for kademe in kademeler
                ),
                Decimal("0"),
            )
        )

        basari_orani = round(
            min(
                100.0,
                float(
                    gerceklesen_tutar
                    / ayrilan_toplam
                    * Decimal("100")
                )
                if ayrilan_toplam > 0
                else 0.0,
            ),
            3,
        )

        kanit = {
            "plan_id": plan_id,
            "sembol": sembol.upper(),
            "kademe_turu": (
                kademe_turu.value
            ),
            "toplam_butce": str(
                butce
            ),
            "kademeler": [
                kademe.as_dict()
                for kademe in kademeler
            ],
            "ortalama_maliyet": (
                str(ortalama_maliyet)
                if ortalama_maliyet
                is not None
                else None
            ),
        }

        return KademePlani(
            plan_id=plan_id,
            sembol=sembol.upper(),
            kademe_turu=kademe_turu,
            toplam_butce=butce,
            kademeler=tuple(
                kademeler
            ),
            gerceklesen_adet=(
                gerceklesen_adet
            ),
            gerceklesen_tutar=(
                gerceklesen_tutar
            ),
            ortalama_maliyet=(
                ortalama_maliyet
            ),
            gerceklesme_orani=(
                gerceklesme_orani
            ),
            basari_orani=(
                basari_orani
            ),
            plan_sha256=_muhur(
                kanit
            ),
        )

    def kasif_yorumu_uret(
        self,
        *,
        aday: VarlikAdayi,
    ) -> KasifFinansYorumu:
        if aday.yonelim == (
            KararYonelimi.GUCLU_ADAY
        ):
            yorum = (
                "Mevcut kanıtlar güçlü bir "
                "aday görünümüne işaret ediyor."
            )

        elif aday.yonelim == (
            KararYonelimi.IZLE
        ):
            yorum = (
                "Olumlu göstergeler var; "
                "fiyat ve yeni kanıtlar izlenmeli."
            )

        elif aday.yonelim == (
            KararYonelimi.TEMKINLI
        ):
            yorum = (
                "Veriler karışık; temkinli ve "
                "kademeli yaklaşım daha uygundur."
            )

        else:
            yorum = (
                "Mevcut risk ve kanıt dengesi "
                "bu aşamada zayıf görünüyor."
            )

        kanit_ozeti = (
            (
                "Güven puanı: "
                f"{aday.guven_puani:.1f}"
            ),
            (
                "Kanıt gücü: "
                f"{aday.kanit_gucu:.1f}"
            ),
            (
                "Risk puanı: "
                f"{aday.risk_puani:.1f}"
            ),
            (
                "Piyasa davranışı: "
                f"{aday.piyasa_davranis_puani:.1f}"
            ),
            (
                "Trend puanı: "
                f"{aday.trend_puani:.1f}"
            ),
        )

        risk_uyarisi = (
            "Risk puanı yüksektir; "
            "sermaye dağılımı sınırlandırılmalıdır."
            if aday.risk_puani >= 70
            else (
                "Risk düzeyi karar planında "
                "dikkate alınmıştır."
            )
        )

        kanit = {
            "sembol": aday.sembol.upper(),
            "karar_puani": (
                aday.karar_puani
            ),
            "yonelim": (
                aday.yonelim.value
            ),
            "yorum": yorum,
            "kanit_ozeti": list(
                kanit_ozeti
            ),
        }

        return KasifFinansYorumu(
            sembol=aday.sembol.upper(),
            karar_puani=(
                aday.karar_puani
            ),
            yonelim=aday.yonelim,
            kisa_yorum=yorum,
            kanit_ozeti=(
                kanit_ozeti
            ),
            risk_uyarisi=(
                risk_uyarisi
            ),
            kesinlik_uyarisi=(
                "Bu değerlendirme kesin sonuç "
                "veya otomatik emir değildir. "
                "Nihai karar kullanıcıya aittir."
            ),
            yorum_sha256=_muhur(
                kanit
            ),
        )