from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .finans_gorunumleri import (
    FinansGorunumMotoru,
    KapBildirimKarti,
    KasaGorunumKarti,
    KaynakSaglikKarti,
    PiyasaGorunumKarti,
)
from .finans_grafik_gecmisi import (
    FinansGrafikMotoru,
    GrafikDonemi,
)
from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _ondalik(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


class FinansSekmesi(StrEnum):
    PIYASA = "piyasa"
    KASAM = "kasam"
    ANALIZ = "analiz"
    PLANLAR = "planlar"


class EkranSinifi(StrEnum):
    TELEFON = "telefon"
    TABLET = "tablet"
    MASAUSTU = "masaustu"


class BilgiSatiriDurumu(StrEnum):
    CANLI = "canli"
    GECIKMELI = "gecikmeli"
    CEVRIMDISI = "cevrimdisi"
    KISMEN_HAZIR = "kismen_hazir"
    VERI_YOK = "veri_yok"


@dataclass(frozen=True, slots=True)
class FinansBilgiSatiri:
    durum: BilgiSatiriDurumu
    baslik: str
    aciklama: str
    son_guncelleme: str
    gecikme_saniyesi: int | None
    kaynak_sayisi: int
    kanit_sha256: str

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "durum": self.durum.value,
            "baslik": self.baslik,
            "aciklama": self.aciklama,
            "son_guncelleme": (
                self.son_guncelleme
            ),
            "gecikme_saniyesi": (
                self.gecikme_saniyesi
            ),
            "kaynak_sayisi": (
                self.kaynak_sayisi
            ),
            "kanit_sha256": (
                self.kanit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class AnalizOzetKarti:
    sembol: str
    varlik_turu: VarlikTuru
    guncel_fiyat: Decimal
    ortalama_maliyet: Decimal | None
    kar_zarar: Decimal | None
    kar_zarar_orani: float | None
    risk_puani: float | None
    guven_puani: float | None
    kanit_gucu: float | None
    aciklama: str
    kanit_sha256: str

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "guncel_fiyat": float(
                self.guncel_fiyat
            ),
            "ortalama_maliyet": (
                float(
                    self.ortalama_maliyet
                )
                if self.ortalama_maliyet
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
            "risk_puani": (
                self.risk_puani
            ),
            "guven_puani": (
                self.guven_puani
            ),
            "kanit_gucu": (
                self.kanit_gucu
            ),
            "aciklama": self.aciklama,
            "kanit_sha256": (
                self.kanit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class PlanGorunumKarti:
    plan_id: str
    sembol: str
    plan_turu: str
    toplam_butce: Decimal
    kademe_sayisi: int
    gerceklesen_kademe_sayisi: int
    gerceklesme_orani: float
    ortalama_maliyet: Decimal | None
    durum: str
    kanit_sha256: str

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "sembol": self.sembol,
            "plan_turu": self.plan_turu,
            "toplam_butce": float(
                self.toplam_butce
            ),
            "kademe_sayisi": (
                self.kademe_sayisi
            ),
            "gerceklesen_kademe_sayisi": (
                self.gerceklesen_kademe_sayisi
            ),
            "gerceklesme_orani": (
                self.gerceklesme_orani
            ),
            "ortalama_maliyet": (
                float(
                    self.ortalama_maliyet
                )
                if self.ortalama_maliyet
                is not None
                else None
            ),
            "durum": self.durum,
            "kanit_sha256": (
                self.kanit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class FinansSekmePaketi:
    sekme: FinansSekmesi
    ekran_sinifi: EkranSinifi
    bilgi_satiri: FinansBilgiSatiri
    kartlar: tuple[
        Mapping[str, Any],
        ...
    ]
    grafikler: tuple[
        Mapping[str, Any],
        ...
    ]
    uretilme_zamani: str
    paket_sha256: str

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "schema": (
                "syfinans-sekme-paketi/v1"
            ),
            "sekme": self.sekme.value,
            "ekran_sinifi": (
                self.ekran_sinifi.value
            ),
            "bilgi_satiri": (
                self.bilgi_satiri
                .as_dict()
            ),
            "kartlar": [
                dict(kart)
                for kart in self.kartlar
            ],
            "grafikler": [
                dict(grafik)
                for grafik in self.grafikler
            ],
            "uretilme_zamani": (
                self.uretilme_zamani
            ),
            "paket_sha256": (
                self.paket_sha256
            ),
        }


class FinansArayuzMotoru:
    def __init__(
        self,
        *,
        gorunum_motoru: FinansGorunumMotoru,
        grafik_motoru: (
            FinansGrafikMotoru | None
        ) = None,
    ) -> None:
        self.gorunum_motoru = (
            gorunum_motoru
        )
        self.grafik_motoru = (
            grafik_motoru
        )

    @staticmethod
    def _ekran_sinifi(
        *,
        genislik: int,
    ) -> EkranSinifi:
        if genislik < 600:
            return EkranSinifi.TELEFON

        if genislik < 1100:
            return EkranSinifi.TABLET

        return EkranSinifi.MASAUSTU

    @staticmethod
    def _bilgi_satiri_uret(
        *,
        piyasa_kartlari: Iterable[
            PiyasaGorunumKarti
        ] = (),
        kaynak_kartlari: Iterable[
            KaynakSaglikKarti
        ] = (),
    ) -> FinansBilgiSatiri:
        piyasa = tuple(
            piyasa_kartlari
        )
        kaynaklar = tuple(
            kaynak_kartlari
        )

        durumlar = {
            kart.veri_akis_durumu
            for kart in piyasa
        }

        hata_sayisi = sum(
            kart.durum
            == "erisilemiyor"
            for kart in kaynaklar
        )

        if (
            VeriAkisDurumu.CEVRIMDISI
            in durumlar
        ):
            durum = (
                BilgiSatiriDurumu
                .CEVRIMDISI
            )
            baslik = (
                "Son güvenilir veri"
            )
            aciklama = (
                "İnternet veya veri kaynağı "
                "kullanılamıyor. Son güvenilir "
                "kayıtlar gösteriliyor."
            )
            gecikme = None

        elif (
            VeriAkisDurumu.GECIKMELI
            in durumlar
        ):
            durum = (
                BilgiSatiriDurumu
                .GECIKMELI
            )
            baslik = (
                "Gecikmeli veri"
            )
            aciklama = (
                "Bazı finans verileri kaynak "
                "gecikmesiyle gösteriliyor."
            )
            gecikme = 60

        elif piyasa:
            durum = (
                BilgiSatiriDurumu.CANLI
            )
            baslik = "Canlı veri"
            aciklama = (
                "Finans verileri kullanılabilir "
                "kaynaklardan güncellendi."
            )
            gecikme = 0

        elif hata_sayisi > 0:
            durum = (
                BilgiSatiriDurumu
                .KISMEN_HAZIR
            )
            baslik = (
                "Kaynaklar kısmen hazır"
            )
            aciklama = (
                "Bazı finans kaynaklarına "
                "erişilemiyor."
            )
            gecikme = None

        else:
            durum = (
                BilgiSatiriDurumu
                .VERI_YOK
            )
            baslik = "Veri bekleniyor"
            aciklama = (
                "Henüz görüntülenecek finans "
                "verisi alınmadı."
            )
            gecikme = None

        zaman = _simdi()

        kanit = {
            "durum": durum.value,
            "baslik": baslik,
            "aciklama": aciklama,
            "kaynaklar": [
                kart.as_dict()
                for kart in kaynaklar
            ],
            "piyasa": [
                kart.kanit_sha256
                for kart in piyasa
            ],
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return FinansBilgiSatiri(
            durum=durum,
            baslik=baslik,
            aciklama=aciklama,
            son_guncelleme=zaman,
            gecikme_saniyesi=gecikme,
            kaynak_sayisi=len(
                kaynaklar
            ),
            kanit_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    @staticmethod
    def _paket_muhurle(
        *,
        sekme: FinansSekmesi,
        ekran_sinifi: EkranSinifi,
        bilgi_satiri: FinansBilgiSatiri,
        kartlar: Iterable[
            Mapping[str, Any]
        ],
        grafikler: Iterable[
            Mapping[str, Any]
        ],
        uretilme_zamani: str,
    ) -> str:
        kanit = {
            "sekme": sekme.value,
            "ekran_sinifi": (
                ekran_sinifi.value
            ),
            "bilgi_satiri": (
                bilgi_satiri.as_dict()
            ),
            "kartlar": [
                dict(kart)
                for kart in kartlar
            ],
            "grafikler": [
                dict(grafik)
                for grafik in grafikler
            ],
            "uretilme_zamani": (
                uretilme_zamani
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return sha256(
            kodlu
        ).hexdigest()

    def piyasa_sekmesi(
        self,
        *,
        varliklar: Iterable[
            tuple[str, VarlikTuru]
        ],
        ekran_genisligi: int,
        grafik_donemi: GrafikDonemi = (
            GrafikDonemi.GUNLUK
        ),
    ) -> FinansSekmePaketi:
        ekran = self._ekran_sinifi(
            genislik=ekran_genisligi
        )

        piyasa_kartlari = tuple(
            self.gorunum_motoru
            .piyasa_karti_uret(
                sembol=sembol,
                varlik_turu=varlik_turu,
            )
            for sembol, varlik_turu
            in varliklar
        )

        saglik_kartlari = (
            self.gorunum_motoru
            .kaynak_saglik_kartlari()
        )

        bilgi_satiri = (
            self._bilgi_satiri_uret(
                piyasa_kartlari=(
                    piyasa_kartlari
                ),
                kaynak_kartlari=(
                    saglik_kartlari
                ),
            )
        )

        grafikler: list[
            Mapping[str, Any]
        ] = []

        if self.grafik_motoru is not None:
            for kart in piyasa_kartlari:
                try:
                    grafikler.append(
                        self.grafik_motoru
                        .ekran_ciktisi(
                            sembol=kart.sembol,
                            donem=(
                                grafik_donemi
                            ),
                        )
                    )
                except ValueError:
                    continue

        kartlar = tuple(
            kart.as_dict()
            for kart in piyasa_kartlari
        ) + tuple(
            {
                "kart_turu": (
                    "kaynak_sagligi"
                ),
                **kart.as_dict(),
            }
            for kart in saglik_kartlari
        )

        uretilme_zamani = _simdi()

        paket_sha256 = (
            self._paket_muhurle(
                sekme=FinansSekmesi.PIYASA,
                ekran_sinifi=ekran,
                bilgi_satiri=(
                    bilgi_satiri
                ),
                kartlar=kartlar,
                grafikler=grafikler,
                uretilme_zamani=(
                    uretilme_zamani
                ),
            )
        )

        return FinansSekmePaketi(
            sekme=FinansSekmesi.PIYASA,
            ekran_sinifi=ekran,
            bilgi_satiri=(
                bilgi_satiri
            ),
            kartlar=kartlar,
            grafikler=tuple(
                grafikler
            ),
            uretilme_zamani=(
                uretilme_zamani
            ),
            paket_sha256=(
                paket_sha256
            ),
        )

    def kasam_sekmesi(
        self,
        *,
        varliklar: Iterable[
            Mapping[str, Any]
        ],
        ekran_genisligi: int,
        grafik_donemi: GrafikDonemi = (
            GrafikDonemi.AYLIK
        ),
    ) -> FinansSekmePaketi:
        ekran = self._ekran_sinifi(
            genislik=ekran_genisligi
        )

        kasa_kartlari: list[
            KasaGorunumKarti
        ] = []

        grafikler: list[
            Mapping[str, Any]
        ] = []

        piyasa_kartlari: list[
            PiyasaGorunumKarti
        ] = []

        for varlik in varliklar:
            kasa = (
                self.gorunum_motoru
                .kasa_karti_uret(
                    sembol=str(
                        varlik["sembol"]
                    ),
                    varlik_turu=(
                        varlik["varlik_turu"]
                    ),
                    miktar=(
                        varlik["miktar"]
                    ),
                    ortalama_maliyet=(
                        varlik[
                            "ortalama_maliyet"
                        ]
                    ),
                )
            )

            kasa_kartlari.append(
                kasa
            )

            piyasa_kartlari.append(
                PiyasaGorunumKarti(
                    sembol=kasa.sembol,
                    varlik_turu=(
                        kasa.varlik_turu
                    ),
                    fiyat=(
                        kasa.guncel_fiyat
                    ),
                    veri_akis_durumu=(
                        kasa
                        .veri_akis_durumu
                    ),
                    kaynaklar=(),
                    aciklama=(
                        "Kasamdaki varlığın "
                        "güncel görünümü."
                    ),
                    kanit_sha256=(
                        kasa.kanit_sha256
                    ),
                )
            )

            if self.grafik_motoru is not None:
                try:
                    grafikler.append(
                        self.grafik_motoru
                        .ekran_ciktisi(
                            sembol=(
                                kasa.sembol
                            ),
                            donem=(
                                grafik_donemi
                            ),
                            ortalama_maliyet=(
                                kasa
                                .ortalama_maliyet
                            ),
                            miktar=(
                                kasa.miktar
                            ),
                        )
                    )
                except ValueError:
                    continue

        saglik_kartlari = (
            self.gorunum_motoru
            .kaynak_saglik_kartlari()
        )

        bilgi_satiri = (
            self._bilgi_satiri_uret(
                piyasa_kartlari=(
                    piyasa_kartlari
                ),
                kaynak_kartlari=(
                    saglik_kartlari
                ),
            )
        )

        kartlar = tuple(
            kart.as_dict()
            for kart in kasa_kartlari
        )

        uretilme_zamani = _simdi()

        paket_sha256 = (
            self._paket_muhurle(
                sekme=FinansSekmesi.KASAM,
                ekran_sinifi=ekran,
                bilgi_satiri=(
                    bilgi_satiri
                ),
                kartlar=kartlar,
                grafikler=grafikler,
                uretilme_zamani=(
                    uretilme_zamani
                ),
            )
        )

        return FinansSekmePaketi(
            sekme=FinansSekmesi.KASAM,
            ekran_sinifi=ekran,
            bilgi_satiri=(
                bilgi_satiri
            ),
            kartlar=kartlar,
            grafikler=tuple(
                grafikler
            ),
            uretilme_zamani=(
                uretilme_zamani
            ),
            paket_sha256=(
                paket_sha256
            ),
        )

    def analiz_sekmesi(
        self,
        *,
        analizler: Iterable[
            Mapping[str, Any]
        ],
        ekran_genisligi: int,
    ) -> FinansSekmePaketi:
        ekran = self._ekran_sinifi(
            genislik=ekran_genisligi
        )

        kartlar: list[
            Mapping[str, Any]
        ] = []

        for analiz in analizler:
            sembol = str(
                analiz["sembol"]
            ).strip().upper()

            varlik_turu = (
                analiz["varlik_turu"]
            )

            guncel_fiyat = _ondalik(
                analiz["guncel_fiyat"]
            )

            ortalama_maliyet = (
                _ondalik(
                    analiz[
                        "ortalama_maliyet"
                    ]
                )
                if analiz.get(
                    "ortalama_maliyet"
                ) is not None
                else None
            )

            kar_zarar = (
                _ondalik(
                    analiz["kar_zarar"]
                )
                if analiz.get(
                    "kar_zarar"
                ) is not None
                else None
            )

            kanit = {
                "sembol": sembol,
                "varlik_turu": (
                    varlik_turu.value
                ),
                "guncel_fiyat": str(
                    guncel_fiyat
                ),
                "ortalama_maliyet": (
                    str(ortalama_maliyet)
                    if ortalama_maliyet
                    is not None
                    else None
                ),
                "risk_puani": analiz.get(
                    "risk_puani"
                ),
                "guven_puani": analiz.get(
                    "guven_puani"
                ),
                "kanit_gucu": analiz.get(
                    "kanit_gucu"
                ),
            }

            kodlu = json.dumps(
                kanit,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            kart = AnalizOzetKarti(
                sembol=sembol,
                varlik_turu=(
                    varlik_turu
                ),
                guncel_fiyat=(
                    guncel_fiyat
                ),
                ortalama_maliyet=(
                    ortalama_maliyet
                ),
                kar_zarar=kar_zarar,
                kar_zarar_orani=(
                    float(
                        analiz[
                            "kar_zarar_orani"
                        ]
                    )
                    if analiz.get(
                        "kar_zarar_orani"
                    ) is not None
                    else None
                ),
                risk_puani=(
                    float(
                        analiz[
                            "risk_puani"
                        ]
                    )
                    if analiz.get(
                        "risk_puani"
                    ) is not None
                    else None
                ),
                guven_puani=(
                    float(
                        analiz[
                            "guven_puani"
                        ]
                    )
                    if analiz.get(
                        "guven_puani"
                    ) is not None
                    else None
                ),
                kanit_gucu=(
                    float(
                        analiz[
                            "kanit_gucu"
                        ]
                    )
                    if analiz.get(
                        "kanit_gucu"
                    ) is not None
                    else None
                ),
                aciklama=str(
                    analiz.get(
                        "aciklama",
                        (
                            "Kanıtlar üzerinden "
                            "oluşturulan karar "
                            "desteği özeti."
                        ),
                    )
                ),
                kanit_sha256=sha256(
                    kodlu
                ).hexdigest(),
            )

            kartlar.append(
                kart.as_dict()
            )

        bilgi_satiri = (
            self._bilgi_satiri_uret()
        )

        uretilme_zamani = _simdi()

        paket_sha256 = (
            self._paket_muhurle(
                sekme=(
                    FinansSekmesi.ANALIZ
                ),
                ekran_sinifi=ekran,
                bilgi_satiri=(
                    bilgi_satiri
                ),
                kartlar=kartlar,
                grafikler=(),
                uretilme_zamani=(
                    uretilme_zamani
                ),
            )
        )

        return FinansSekmePaketi(
            sekme=FinansSekmesi.ANALIZ,
            ekran_sinifi=ekran,
            bilgi_satiri=(
                bilgi_satiri
            ),
            kartlar=tuple(
                kartlar
            ),
            grafikler=(),
            uretilme_zamani=(
                uretilme_zamani
            ),
            paket_sha256=(
                paket_sha256
            ),
        )

    def planlar_sekmesi(
        self,
        *,
        planlar: Iterable[
            Mapping[str, Any]
        ],
        ekran_genisligi: int,
    ) -> FinansSekmePaketi:
        ekran = self._ekran_sinifi(
            genislik=ekran_genisligi
        )

        kartlar: list[
            Mapping[str, Any]
        ] = []

        for plan in planlar:
            kademe_sayisi = int(
                plan["kademe_sayisi"]
            )

            gerceklesen = int(
                plan[
                    "gerceklesen_kademe_sayisi"
                ]
            )

            oran = (
                round(
                    gerceklesen
                    / kademe_sayisi
                    * 100.0,
                    3,
                )
                if kademe_sayisi > 0
                else 0.0
            )

            kanit = {
                "plan_id": str(
                    plan["plan_id"]
                ),
                "sembol": str(
                    plan["sembol"]
                ).upper(),
                "plan_turu": str(
                    plan["plan_turu"]
                ),
                "toplam_butce": str(
                    _ondalik(
                        plan[
                            "toplam_butce"
                        ]
                    )
                ),
                "kademe_sayisi": (
                    kademe_sayisi
                ),
                "gerceklesen": gerceklesen,
                "ortalama_maliyet": (
                    str(
                        _ondalik(
                            plan[
                                "ortalama_maliyet"
                            ]
                        )
                    )
                    if plan.get(
                        "ortalama_maliyet"
                    ) is not None
                    else None
                ),
            }

            kodlu = json.dumps(
                kanit,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            kart = PlanGorunumKarti(
                plan_id=str(
                    plan["plan_id"]
                ),
                sembol=str(
                    plan["sembol"]
                ).strip().upper(),
                plan_turu=str(
                    plan["plan_turu"]
                ),
                toplam_butce=_ondalik(
                    plan["toplam_butce"]
                ),
                kademe_sayisi=(
                    kademe_sayisi
                ),
                gerceklesen_kademe_sayisi=(
                    gerceklesen
                ),
                gerceklesme_orani=oran,
                ortalama_maliyet=(
                    _ondalik(
                        plan[
                            "ortalama_maliyet"
                        ]
                    )
                    if plan.get(
                        "ortalama_maliyet"
                    ) is not None
                    else None
                ),
                durum=str(
                    plan.get(
                        "durum",
                        "izleniyor",
                    )
                ),
                kanit_sha256=sha256(
                    kodlu
                ).hexdigest(),
            )

            kartlar.append(
                kart.as_dict()
            )

        bilgi_satiri = (
            self._bilgi_satiri_uret()
        )

        uretilme_zamani = _simdi()

        paket_sha256 = (
            self._paket_muhurle(
                sekme=(
                    FinansSekmesi.PLANLAR
                ),
                ekran_sinifi=ekran,
                bilgi_satiri=(
                    bilgi_satiri
                ),
                kartlar=kartlar,
                grafikler=(),
                uretilme_zamani=(
                    uretilme_zamani
                ),
            )
        )

        return FinansSekmePaketi(
            sekme=FinansSekmesi.PLANLAR,
            ekran_sinifi=ekran,
            bilgi_satiri=(
                bilgi_satiri
            ),
            kartlar=tuple(
                kartlar
            ),
            grafikler=(),
            uretilme_zamani=(
                uretilme_zamani
            ),
            paket_sha256=(
                paket_sha256
            ),
        )

    def kap_kartlari(
        self,
        *,
        sembol: str | None = None,
        limit: int = 20,
    ) -> tuple[
        KapBildirimKarti,
        ...
    ]:
        return (
            self.gorunum_motoru
            .kap_kartlari_uret(
                sembol=sembol,
                limit=limit,
            )
        )