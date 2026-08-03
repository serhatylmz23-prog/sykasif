from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Iterable


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.01")
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


class ArgeVarlikTuru(StrEnum):
    PARCA = "parca"
    SARF_MALZEMESI = "sarf_malzemesi"
    BAKIM = "bakim"
    YAZILIM = "yazilim"
    HIZMET = "hizmet"
    DIGER = "diger"


class ArgeDurumu(StrEnum):
    AKTIF = "aktif"
    BAKIM_GEREKIYOR = "bakim_gerekiyor"
    YENILEME_ADAYI = "yenileme_adayi"
    GARANTI_SONA_YAKIN = "garanti_sona_yakin"
    KRITIK = "kritik"
    PASIF = "pasif"


class ArgeOneriTuru(StrEnum):
    IZLE = "izle"
    BAKIM = "bakim"
    YENILE = "yenile"
    ARASTIR = "arastir"
    TEDARIKCI_KARSILASTIR = (
        "tedarikci_karsilastir"
    )
    BUTCE_AYIR = "butce_ayir"


@dataclass(frozen=True, slots=True)
class FiyatKaydi:
    tarih: str
    fiyat: Decimal
    para_birimi: str
    kaynak: str

    def __post_init__(self) -> None:
        if self.fiyat <= 0:
            raise ValueError(
                "Fiyat pozitif olmalıdır."
            )

        date.fromisoformat(
            self.tarih
        )

        if not self.para_birimi.strip():
            raise ValueError(
                "Para birimi boş olamaz."
            )

        if not self.kaynak.strip():
            raise ValueError(
                "Fiyat kaynağı boş olamaz."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "tarih": self.tarih,
            "fiyat": float(
                self.fiyat
            ),
            "para_birimi": (
                self.para_birimi
            ),
            "kaynak": self.kaynak,
        }


@dataclass(frozen=True, slots=True)
class TedarikciKaydi:
    tedarikci_id: str
    ad: str
    ulke: str
    guven_puani: float
    garanti_puani: float
    teslimat_puani: float
    servis_puani: float
    fiyat_puani: float
    dogrulanmis_kaynak_sayisi: int
    aciklama: str = ""

    @property
    def genel_puan(self) -> float:
        kaynak_katsayisi = min(
            1.0,
            self.dogrulanmis_kaynak_sayisi
            / 5.0,
        )

        temel = (
            _sinirla(
                self.guven_puani
            )
            * 0.30
            + _sinirla(
                self.garanti_puani
            )
            * 0.20
            + _sinirla(
                self.teslimat_puani
            )
            * 0.15
            + _sinirla(
                self.servis_puani
            )
            * 0.20
            + _sinirla(
                self.fiyat_puani
            )
            * 0.15
        )

        return _sinirla(
            temel
            * (
                0.80
                + kaynak_katsayisi
                * 0.20
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "tedarikci_id": (
                self.tedarikci_id
            ),
            "ad": self.ad,
            "ulke": self.ulke,
            "guven_puani": _sinirla(
                self.guven_puani
            ),
            "garanti_puani": _sinirla(
                self.garanti_puani
            ),
            "teslimat_puani": _sinirla(
                self.teslimat_puani
            ),
            "servis_puani": _sinirla(
                self.servis_puani
            ),
            "fiyat_puani": _sinirla(
                self.fiyat_puani
            ),
            "dogrulanmis_kaynak_sayisi": (
                self
                .dogrulanmis_kaynak_sayisi
            ),
            "genel_puan": (
                self.genel_puan
            ),
            "aciklama": self.aciklama,
        }


@dataclass(frozen=True, slots=True)
class ArgeVarligi:
    varlik_id: str
    ad: str
    tur: ArgeVarlikTuru
    kategori: str
    mevcut_surumu: str
    edinme_tarihi: str
    edinme_maliyeti: Decimal
    garanti_bitis_tarihi: str | None
    son_bakim_tarihi: str | None
    sonraki_bakim_tarihi: str | None
    performans_puani: float
    guvenilirlik_puani: float
    kritik_onem_puani: float
    uyumluluk_puani: float
    enerji_verimliligi_puani: float
    durum: ArgeDurumu
    fiyat_gecmisi: tuple[
        FiyatKaydi,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if not self.varlik_id.strip():
            raise ValueError(
                "Ar-Ge varlık kimliği boş olamaz."
            )

        if not self.ad.strip():
            raise ValueError(
                "Ar-Ge varlık adı boş olamaz."
            )

        if self.edinme_maliyeti < 0:
            raise ValueError(
                "Edinme maliyeti negatif olamaz."
            )

        date.fromisoformat(
            self.edinme_tarihi
        )

        for tarih in (
            self.garanti_bitis_tarihi,
            self.son_bakim_tarihi,
            self.sonraki_bakim_tarihi,
        ):
            if tarih is not None:
                date.fromisoformat(
                    tarih
                )

    @property
    def zayiflik_puani(self) -> float:
        performans_acigi = (
            100.0
            - _sinirla(
                self.performans_puani
            )
        )

        guvenilirlik_acigi = (
            100.0
            - _sinirla(
                self.guvenilirlik_puani
            )
        )

        uyumluluk_acigi = (
            100.0
            - _sinirla(
                self.uyumluluk_puani
            )
        )

        enerji_acigi = (
            100.0
            - _sinirla(
                self
                .enerji_verimliligi_puani
            )
        )

        kritik_katsayi = (
            0.60
            + _sinirla(
                self.kritik_onem_puani
            )
            / 250.0
        )

        durum_artisi = {
            ArgeDurumu.AKTIF: 0.0,
            ArgeDurumu.BAKIM_GEREKIYOR: 8.0,
            ArgeDurumu.YENILEME_ADAYI: 15.0,
            ArgeDurumu.GARANTI_SONA_YAKIN: 5.0,
            ArgeDurumu.KRITIK: 25.0,
            ArgeDurumu.PASIF: 0.0,
        }[
            self.durum
        ]

        return _sinirla(
            (
                performans_acigi
                * 0.32
                + guvenilirlik_acigi
                * 0.30
                + uyumluluk_acigi
                * 0.23
                + enerji_acigi
                * 0.15
            )
            * kritik_katsayi
            + durum_artisi
        )

    @property
    def son_fiyat(
        self,
    ) -> Decimal | None:
        if not self.fiyat_gecmisi:
            return None

        son = max(
            self.fiyat_gecmisi,
            key=lambda kayit: (
                kayit.tarih
            ),
        )

        return son.fiyat

    @property
    def fiyat_degisim_orani(
        self,
    ) -> float | None:
        if len(
            self.fiyat_gecmisi
        ) < 2:
            return None

        sirali = sorted(
            self.fiyat_gecmisi,
            key=lambda kayit: (
                kayit.tarih
            ),
        )

        ilk = Decimal(
            str(
                sirali[0].fiyat
            )
        )

        son = Decimal(
            str(
                sirali[-1].fiyat
            )
        )

        if ilk <= 0:
            return None

        degisim = (
            (
                son - ilk
            )
            / ilk
            * Decimal("100")
        )

        return round(
            float(
                degisim
            ),
            3,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "varlik_id": self.varlik_id,
            "ad": self.ad,
            "tur": self.tur.value,
            "kategori": self.kategori,
            "mevcut_surumu": (
                self.mevcut_surumu
            ),
            "edinme_tarihi": (
                self.edinme_tarihi
            ),
            "edinme_maliyeti": float(
                self.edinme_maliyeti
            ),
            "garanti_bitis_tarihi": (
                self.garanti_bitis_tarihi
            ),
            "son_bakim_tarihi": (
                self.son_bakim_tarihi
            ),
            "sonraki_bakim_tarihi": (
                self.sonraki_bakim_tarihi
            ),
            "performans_puani": _sinirla(
                self.performans_puani
            ),
            "guvenilirlik_puani": (
                _sinirla(
                    self.guvenilirlik_puani
                )
            ),
            "kritik_onem_puani": (
                _sinirla(
                    self.kritik_onem_puani
                )
            ),
            "uyumluluk_puani": (
                _sinirla(
                    self.uyumluluk_puani
                )
            ),
            "enerji_verimliligi_puani": (
                _sinirla(
                    self
                    .enerji_verimliligi_puani
                )
            ),
            "durum": self.durum.value,
            "zayiflik_puani": (
                self.zayiflik_puani
            ),
            "son_fiyat": (
                float(self.son_fiyat)
                if self.son_fiyat
                is not None
                else None
            ),
            "fiyat_degisim_orani": (
                self.fiyat_degisim_orani
            ),
            "fiyat_gecmisi": [
                kayit.as_dict()
                for kayit
                in self.fiyat_gecmisi
            ],
        }


@dataclass(frozen=True, slots=True)
class ArgeOnerisi:
    oneri_id: str
    varlik_id: str | None
    oneri_turu: ArgeOneriTuru
    baslik: str
    aciklama: str
    oncelik_puani: float
    tahmini_maliyet: Decimal
    beklenen_fayda_puani: float
    kanitlar: tuple[str, ...]
    tedarikci_adaylari: tuple[
        TedarikciKaydi,
        ...
    ] = ()

    @property
    def fayda_maliyet_puani(self) -> float:
        maliyet_cezasi = min(
            50.0,
            float(
                self.tahmini_maliyet
                / Decimal("10000")
            )
            * 10.0,
        )

        return _sinirla(
            self.beklenen_fayda_puani
            * 0.70
            + self.oncelik_puani
            * 0.30
            - maliyet_cezasi
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "oneri_id": self.oneri_id,
            "varlik_id": self.varlik_id,
            "oneri_turu": (
                self.oneri_turu.value
            ),
            "baslik": self.baslik,
            "aciklama": self.aciklama,
            "oncelik_puani": _sinirla(
                self.oncelik_puani
            ),
            "tahmini_maliyet": float(
                self.tahmini_maliyet
            ),
            "beklenen_fayda_puani": (
                _sinirla(
                    self.beklenen_fayda_puani
                )
            ),
            "fayda_maliyet_puani": (
                self.fayda_maliyet_puani
            ),
            "kanitlar": list(
                self.kanitlar
            ),
            "tedarikci_adaylari": [
                tedarikci.as_dict()
                for tedarikci
                in self.tedarikci_adaylari
            ],
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
        }


@dataclass(frozen=True, slots=True)
class ArgeDegerlendirmesi:
    varliklar: tuple[
        ArgeVarligi,
        ...
    ]
    oneriler: tuple[
        ArgeOnerisi,
        ...
    ]
    toplam_arge_butcesi: Decimal
    kullanilabilir_butce: Decimal
    en_zayif_varlik_id: str | None
    degerlendirme_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "varlik_sayisi": len(
                self.varliklar
            ),
            "oneri_sayisi": len(
                self.oneriler
            ),
            "toplam_arge_butcesi": float(
                self.toplam_arge_butcesi
            ),
            "kullanilabilir_butce": float(
                self.kullanilabilir_butce
            ),
            "en_zayif_varlik_id": (
                self.en_zayif_varlik_id
            ),
            "varliklar": [
                varlik.as_dict()
                for varlik
                in self.varliklar
            ],
            "oneriler": [
                oneri.as_dict()
                for oneri
                in self.oneriler
            ],
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
            "degerlendirme_sha256": (
                self.degerlendirme_sha256
            ),
        }


class SyKasifArgeMotoru:
    @classmethod
    def degerlendir(
        cls,
        *,
        varliklar: Iterable[
            ArgeVarligi
        ],
        tedarikciler: Iterable[
            TedarikciKaydi
        ] = (),
        toplam_arge_butcesi: (
            Decimal | int | float | str
        ),
        finans_butce_fazlasi: (
            Decimal | int | float | str
        ) = 0,
        asgari_nakit_guvenligi: (
            Decimal | int | float | str
        ) = 0,
    ) -> ArgeDegerlendirmesi:
        varlik_listesi = tuple(
            varliklar
        )

        if not varlik_listesi:
            raise ValueError(
                "En az bir SyKaşif Ar-Ge "
                "varlığı gereklidir."
            )

        kimlikler = [
            varlik.varlik_id
            for varlik in varlik_listesi
        ]

        if len(
            set(kimlikler)
        ) != len(kimlikler):
            raise ValueError(
                "Aynı Ar-Ge varlık kimliği "
                "birden fazla kullanılamaz."
            )

        butce = _para(
            toplam_arge_butcesi
        )

        fazlalik = _para(
            finans_butce_fazlasi
        )

        nakit_guvenligi = _para(
            asgari_nakit_guvenligi
        )

        if butce < 0:
            raise ValueError(
                "Ar-Ge bütçesi negatif olamaz."
            )

        if fazlalik < 0:
            raise ValueError(
                "Finans bütçe fazlası "
                "negatif olamaz."
            )

        if nakit_guvenligi < 0:
            raise ValueError(
                "Asgari nakit güvenliği "
                "negatif olamaz."
            )

        aktarilabilir_fazlalik = max(
            Decimal("0.00"),
            fazlalik
            - nakit_guvenligi,
        )

        kullanilabilir = _para(
            butce
            + aktarilabilir_fazlalik
        )

        tedarikci_listesi = sorted(
            tuple(
                tedarikciler
            ),
            key=lambda tedarikci: (
                tedarikci.genel_puan
            ),
            reverse=True,
        )

        oneriler: list[
            ArgeOnerisi
        ] = []

        sirali_varliklar = sorted(
            varlik_listesi,
            key=lambda varlik: (
                varlik.zayiflik_puani
            ),
            reverse=True,
        )

        for varlik in sirali_varliklar:
            tahmini_maliyet = (
                varlik.son_fiyat
                if varlik.son_fiyat
                is not None
                else varlik.edinme_maliyeti
            )

            if (
                varlik.durum
                == ArgeDurumu.KRITIK
                or varlik.zayiflik_puani
                >= 75
            ):
                tur = (
                    ArgeOneriTuru.YENILE
                )

                baslik = (
                    f"{varlik.ad} için "
                    "yenileme önceliği"
                )

                aciklama = (
                    "Parça kritik zayıflık "
                    "seviyesine ulaştı. Yerli "
                    "tedarikçiler önce, küresel "
                    "alternatifler ikinci aşamada "
                    "karşılaştırılmalıdır."
                )

                fayda = min(
                    100.0,
                    varlik.zayiflik_puani
                    + 15.0,
                )

            elif (
                varlik.durum
                == ArgeDurumu.BAKIM_GEREKIYOR
                or varlik.zayiflik_puani
                >= 55
            ):
                tur = (
                    ArgeOneriTuru.BAKIM
                )

                baslik = (
                    f"{varlik.ad} bakım "
                    "değerlendirmesi"
                )

                aciklama = (
                    "Yenilemeden önce bakım, "
                    "kalibrasyon ve parça değişimi "
                    "seçenekleri karşılaştırılmalıdır."
                )

                fayda = min(
                    90.0,
                    varlik.zayiflik_puani
                    + 10.0,
                )

                tahmini_maliyet = _para(
                    tahmini_maliyet
                    * Decimal("0.20")
                )

            elif (
                varlik.durum
                == ArgeDurumu
                .GARANTI_SONA_YAKIN
            ):
                tur = (
                    ArgeOneriTuru
                    .TEDARIKCI_KARSILASTIR
                )

                baslik = (
                    f"{varlik.ad} garanti "
                    "ve servis araştırması"
                )

                aciklama = (
                    "Garanti bitmeden servis, "
                    "yedek parça ve uzatma "
                    "seçenekleri araştırılmalıdır."
                )

                fayda = 60.0

                tahmini_maliyet = _para(
                    tahmini_maliyet
                    * Decimal("0.10")
                )

            else:
                tur = ArgeOneriTuru.IZLE

                baslik = (
                    f"{varlik.ad} izleme kaydı"
                )

                aciklama = (
                    "Mevcut durumda zorunlu "
                    "yenileme gerekmiyor; fiyat, "
                    "performans ve garanti verileri "
                    "izlenmeye devam edilmelidir."
                )

                fayda = max(
                    25.0,
                    varlik.zayiflik_puani
                )

                tahmini_maliyet = Decimal(
                    "0.00"
                )

            kanitlar = [
                (
                    "Zayıflık puanı: "
                    f"{varlik.zayiflik_puani:.1f}"
                ),
                (
                    "Performans puanı: "
                    f"{varlik.performans_puani:.1f}"
                ),
                (
                    "Güvenilirlik puanı: "
                    f"{varlik.guvenilirlik_puani:.1f}"
                ),
                (
                    "Kritik önem puanı: "
                    f"{varlik.kritik_onem_puani:.1f}"
                ),
            ]

            if (
                varlik.fiyat_degisim_orani
                is not None
            ):
                kanitlar.append(
                    "Fiyat değişimi: "
                    f"%{varlik.fiyat_degisim_orani:.1f}"
                )

            oneriler.append(
                ArgeOnerisi(
                    oneri_id=(
                        "SYF-ARGE-"
                        f"{varlik.varlik_id}"
                    ),
                    varlik_id=(
                        varlik.varlik_id
                    ),
                    oneri_turu=tur,
                    baslik=baslik,
                    aciklama=aciklama,
                    oncelik_puani=(
                        varlik.zayiflik_puani
                    ),
                    tahmini_maliyet=_para(
                        tahmini_maliyet
                    ),
                    beklenen_fayda_puani=(
                        fayda
                    ),
                    kanitlar=tuple(
                        kanitlar
                    ),
                    tedarikci_adaylari=tuple(
                        tedarikci_listesi[:5]
                    ),
                )
            )

        yuksek_oncelikli_maliyet = sum(
            (
                oneri.tahmini_maliyet
                for oneri in oneriler
                if oneri.oneri_turu
                in {
                    ArgeOneriTuru.YENILE,
                    ArgeOneriTuru.BAKIM,
                }
            ),
            Decimal("0.00"),
        )

        if (
            kullanilabilir
            > yuksek_oncelikli_maliyet
            and aktarilabilir_fazlalik
            > 0
        ):
            oneriler.append(
                ArgeOnerisi(
                    oneri_id=(
                        "SYF-ARGE-BUTCE-FAZLASI"
                    ),
                    varlik_id=None,
                    oneri_turu=(
                        ArgeOneriTuru.BUTCE_AYIR
                    ),
                    baslik=(
                        "Ar-Ge bütçe fazlası "
                        "değerlendirmesi"
                    ),
                    aciklama=(
                        "Nakit güvenlik payı "
                        "korunduktan sonra kalan "
                        "finans bütçe fazlası, "
                        "kullanıcı onayıyla Ar-Ge "
                        "yenileme havuzuna "
                        "aktarılabilir."
                    ),
                    oncelik_puani=55.0,
                    tahmini_maliyet=(
                        aktarilabilir_fazlalik
                    ),
                    beklenen_fayda_puani=65.0,
                    kanitlar=(
                        "Nakit güvenlik payı korundu.",
                        (
                            "Aktarılabilir bütçe: "
                            f"{aktarilabilir_fazlalik}"
                        ),
                    ),
                )
            )

        oneriler = sorted(
            oneriler,
            key=lambda oneri: (
                oneri.oncelik_puani,
                oneri.fayda_maliyet_puani,
            ),
            reverse=True,
        )

        en_zayif = (
            sirali_varliklar[0]
            .varlik_id
            if sirali_varliklar
            else None
        )

        kanit = {
            "varliklar": [
                varlik.as_dict()
                for varlik in varlik_listesi
            ],
            "oneriler": [
                oneri.as_dict()
                for oneri in oneriler
            ],
            "toplam_arge_butcesi": str(
                butce
            ),
            "kullanilabilir_butce": str(
                kullanilabilir
            ),
            "en_zayif_varlik_id": (
                en_zayif
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return ArgeDegerlendirmesi(
            varliklar=varlik_listesi,
            oneriler=tuple(
                oneriler
            ),
            toplam_arge_butcesi=butce,
            kullanilabilir_butce=(
                kullanilabilir
            ),
            en_zayif_varlik_id=(
                en_zayif
            ),
            degerlendirme_sha256=sha256(
                kodlu
            ).hexdigest(),
        )


class SyFinansUcKatmanSozlesmesi:
    @staticmethod
    def ekran_sozlesmesi() -> dict[str, Any]:
        return {
            "katmanlar": [
                {
                    "katman_id": (
                        "piyasa_evreni"
                    ),
                    "baslik": "Piyasa",
                    "aciklama": (
                        "Tüm BIST, fon, döviz "
                        "ve kıymetli madenler."
                    ),
                },
                {
                    "katman_id": (
                        "kullanici_kasasi"
                    ),
                    "baslik": "Kasam",
                    "aciklama": (
                        "Kullanıcının mevcut "
                        "yatırımları ve maliyetleri."
                    ),
                },
                {
                    "katman_id": (
                        "sykasif_arge"
                    ),
                    "baslik": (
                        "SyKaşif Ar-Ge"
                    ),
                    "aciklama": (
                        "Parça, sarf, bakım, "
                        "garanti, tedarikçi, fiyat "
                        "ve yenileme araştırmaları."
                    ),
                },
            ],
            "katmanlar_karismaz": True,
            "ortak_analiz_mevcut": True,
            "finans_fazlasi_argeye_aktarilabilir": (
                True
            ),
            "nihai_karar": "kullanici",
        }