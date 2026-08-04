from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .capraz_dogrulama import (
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
)
from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from .veri_saglayicilari import (
    PiyasaVerisi,
    VeriDogruLamaMotoru,
)


def _ondalik(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


def _zaman_dogrula(
    deger: str,
) -> str:
    metin = str(
        deger
    ).strip()

    if not metin:
        raise ValueError(
            "Zaman damgası boş olamaz."
        )

    try:
        sonuc = datetime.fromisoformat(
            metin.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError as error:
        raise ValueError(
            "Geçersiz zaman damgası."
        ) from error

    if sonuc.tzinfo is None:
        sonuc = sonuc.replace(
            tzinfo=UTC
        )

    return sonuc.isoformat()


class FinansKaynakSinifi(StrEnum):
    BIST = "bist"
    KAP = "kap"
    FON = "fon"
    DOVIZ = "doviz"
    KIYMETLI_MADEN = "kiymetli_maden"


class BildirimOnemi(StrEnum):
    BILGI = "bilgi"
    DIKKAT = "dikkat"
    ONEMLI = "onemli"
    KRITIK = "kritik"


@dataclass(frozen=True, slots=True)
class BistPiyasaKaydi:
    sembol: str
    son_fiyat: Decimal
    alis_fiyati: Decimal | None
    satis_fiyati: Decimal | None
    hacim: Decimal | None
    degisim_orani: float | None
    zaman_damgasi: str
    para_birimi: str = "TRY"

    def __post_init__(self) -> None:
        if not self.sembol.strip():
            raise ValueError(
                "BIST sembolü boş olamaz."
            )

        if self.son_fiyat <= 0:
            raise ValueError(
                "BIST son fiyatı pozitif olmalıdır."
            )

        _zaman_dogrula(
            self.zaman_damgasi
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "son_fiyat": float(
                self.son_fiyat
            ),
            "alis_fiyati": (
                float(self.alis_fiyati)
                if self.alis_fiyati is not None
                else None
            ),
            "satis_fiyati": (
                float(self.satis_fiyati)
                if self.satis_fiyati is not None
                else None
            ),
            "hacim": (
                float(self.hacim)
                if self.hacim is not None
                else None
            ),
            "degisim_orani": (
                self.degisim_orani
            ),
            "zaman_damgasi": (
                self.zaman_damgasi
            ),
            "para_birimi": (
                self.para_birimi
            ),
        }


@dataclass(frozen=True, slots=True)
class KapBildirimi:
    bildirim_id: str
    sembol: str
    baslik: str
    yayin_zamani: str
    bildirim_turu: str
    ozet: str
    kaynak_adresi: str
    onem: BildirimOnemi
    dogrulanmis: bool = False
    bildirim_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.bildirim_id.strip():
            raise ValueError(
                "KAP bildirim kimliği boş olamaz."
            )

        if not self.sembol.strip():
            raise ValueError(
                "KAP sembolü boş olamaz."
            )

        if not self.baslik.strip():
            raise ValueError(
                "KAP başlığı boş olamaz."
            )

        _zaman_dogrula(
            self.yayin_zamani
        )

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
            "bildirim_turu": (
                self.bildirim_turu
            ),
            "ozet": self.ozet,
            "kaynak_adresi": (
                self.kaynak_adresi
            ),
            "onem": self.onem.value,
            "dogrulanmis": (
                self.dogrulanmis
            ),
            "bildirim_sha256": (
                self.bildirim_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class FonKaydi:
    fon_kodu: str
    fon_adi: str
    birim_fiyat: Decimal
    toplam_deger: Decimal | None
    yatirimci_sayisi: int | None
    portfoy_dagilimi: Mapping[str, float]
    zaman_damgasi: str
    para_birimi: str = "TRY"

    def __post_init__(self) -> None:
        if not self.fon_kodu.strip():
            raise ValueError(
                "Fon kodu boş olamaz."
            )

        if self.birim_fiyat <= 0:
            raise ValueError(
                "Fon birim fiyatı pozitif olmalıdır."
            )

        _zaman_dogrula(
            self.zaman_damgasi
        )

        toplam = sum(
            float(deger)
            for deger
            in self.portfoy_dagilimi.values()
        )

        if (
            self.portfoy_dagilimi
            and not 99.0 <= toplam <= 101.0
        ):
            raise ValueError(
                "Fon portföy dağılımı yaklaşık "
                "yüzde 100 olmalıdır."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "fon_kodu": self.fon_kodu,
            "fon_adi": self.fon_adi,
            "birim_fiyat": float(
                self.birim_fiyat
            ),
            "toplam_deger": (
                float(self.toplam_deger)
                if self.toplam_deger is not None
                else None
            ),
            "yatirimci_sayisi": (
                self.yatirimci_sayisi
            ),
            "portfoy_dagilimi": dict(
                self.portfoy_dagilimi
            ),
            "zaman_damgasi": (
                self.zaman_damgasi
            ),
            "para_birimi": (
                self.para_birimi
            ),
        }


@dataclass(frozen=True, slots=True)
class DovizKaydi:
    kod: str
    alis_fiyati: Decimal
    satis_fiyati: Decimal
    zaman_damgasi: str
    kaynak_turu: str
    para_birimi: str = "TRY"

    def __post_init__(self) -> None:
        if not self.kod.strip():
            raise ValueError(
                "Döviz kodu boş olamaz."
            )

        if (
            self.alis_fiyati <= 0
            or self.satis_fiyati <= 0
        ):
            raise ValueError(
                "Döviz fiyatları pozitif olmalıdır."
            )

        if self.satis_fiyati < self.alis_fiyati:
            raise ValueError(
                "Döviz satış fiyatı alış "
                "fiyatından düşük olamaz."
            )

        _zaman_dogrula(
            self.zaman_damgasi
        )

    @property
    def orta_fiyat(self) -> Decimal:
        return _ondalik(
            (
                self.alis_fiyati
                + self.satis_fiyati
            )
            / Decimal("2")
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kod": self.kod,
            "alis_fiyati": float(
                self.alis_fiyati
            ),
            "satis_fiyati": float(
                self.satis_fiyati
            ),
            "orta_fiyat": float(
                self.orta_fiyat
            ),
            "zaman_damgasi": (
                self.zaman_damgasi
            ),
            "kaynak_turu": (
                self.kaynak_turu
            ),
            "para_birimi": (
                self.para_birimi
            ),
        }


@dataclass(frozen=True, slots=True)
class KiymetliMadenKaydi:
    kod: str
    maden_adi: str
    birim: str
    alis_fiyati: Decimal
    satis_fiyati: Decimal
    zaman_damgasi: str
    para_birimi: str = "TRY"

    def __post_init__(self) -> None:
        if self.kod not in {
            "ALTIN",
            "GUMUS",
        }:
            raise ValueError(
                "Desteklenmeyen kıymetli maden kodu."
            )

        if (
            self.alis_fiyati <= 0
            or self.satis_fiyati <= 0
        ):
            raise ValueError(
                "Maden fiyatları pozitif olmalıdır."
            )

        if self.satis_fiyati < self.alis_fiyati:
            raise ValueError(
                "Maden satış fiyatı alış "
                "fiyatından düşük olamaz."
            )

        _zaman_dogrula(
            self.zaman_damgasi
        )

    @property
    def orta_fiyat(self) -> Decimal:
        return _ondalik(
            (
                self.alis_fiyati
                + self.satis_fiyati
            )
            / Decimal("2")
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kod": self.kod,
            "maden_adi": self.maden_adi,
            "birim": self.birim,
            "alis_fiyati": float(
                self.alis_fiyati
            ),
            "satis_fiyati": float(
                self.satis_fiyati
            ),
            "orta_fiyat": float(
                self.orta_fiyat
            ),
            "zaman_damgasi": (
                self.zaman_damgasi
            ),
            "para_birimi": (
                self.para_birimi
            ),
        }


class GercekKaynakBagdastiricisi(ABC):
    @property
    @abstractmethod
    def saglayici_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def kaynak_sinifi(
        self,
    ) -> FinansKaynakSinifi:
        raise NotImplementedError

    @property
    @abstractmethod
    def guven_profili(
        self,
    ) -> KaynakGuvenProfili:
        raise NotImplementedError


class PiyasaKaynakBagdastiricisi(
    GercekKaynakBagdastiricisi
):
    @abstractmethod
    def piyasa_verisi_getir(
        self,
        *,
        sembol: str,
    ) -> KaynakliPiyasaVerisi:
        raise NotImplementedError


class KapKaynakBagdastiricisi(
    GercekKaynakBagdastiricisi
):
    @abstractmethod
    def bildirimleri_getir(
        self,
        *,
        sembol: str | None = None,
        limit: int = 50,
    ) -> tuple[KapBildirimi, ...]:
        raise NotImplementedError


class DenemeGercekKaynakBagdastiricisi(
    PiyasaKaynakBagdastiricisi
):
    def __init__(
        self,
        *,
        saglayici_id: str,
        kaynak_sinifi: FinansKaynakSinifi,
        guven_profili: KaynakGuvenProfili,
        kayitlar: Mapping[
            str,
            BistPiyasaKaydi
            | FonKaydi
            | DovizKaydi
            | KiymetliMadenKaydi,
        ],
        veri_durumu: VeriAkisDurumu = (
            VeriAkisDurumu.ANLIK
        ),
        gecikme_saniyesi: int = 0,
    ) -> None:
        if (
            guven_profili.saglayici_id
            != saglayici_id
        ):
            raise ValueError(
                "Sağlayıcı ile güven profili "
                "kimliği uyuşmuyor."
            )

        self._saglayici_id = saglayici_id
        self._kaynak_sinifi = kaynak_sinifi
        self._guven_profili = guven_profili
        self.kayitlar = {
            str(kod).strip().upper(): kayit
            for kod, kayit
            in kayitlar.items()
        }
        self.veri_durumu = veri_durumu
        self.gecikme_saniyesi = max(
            0,
            int(gecikme_saniyesi),
        )

    @property
    def saglayici_id(self) -> str:
        return self._saglayici_id

    @property
    def kaynak_sinifi(
        self,
    ) -> FinansKaynakSinifi:
        return self._kaynak_sinifi

    @property
    def guven_profili(
        self,
    ) -> KaynakGuvenProfili:
        return self._guven_profili

    def piyasa_verisi_getir(
        self,
        *,
        sembol: str,
    ) -> KaynakliPiyasaVerisi:
        anahtar = str(
            sembol
        ).strip().upper()

        try:
            kayit = self.kayitlar[
                anahtar
            ]
        except KeyError as error:
            raise KeyError(
                f"Kaynak verisi bulunamadı: {anahtar}"
            ) from error

        if isinstance(
            kayit,
            BistPiyasaKaydi,
        ):
            varlik_turu = VarlikTuru.HISSE
            fiyat = kayit.son_fiyat
            alis = kayit.alis_fiyati
            satis = kayit.satis_fiyati
            hacim = kayit.hacim
            degisim = kayit.degisim_orani
            zaman = kayit.zaman_damgasi
            para_birimi = kayit.para_birimi

        elif isinstance(
            kayit,
            FonKaydi,
        ):
            varlik_turu = VarlikTuru.FON
            fiyat = kayit.birim_fiyat
            alis = None
            satis = None
            hacim = kayit.toplam_deger
            degisim = None
            zaman = kayit.zaman_damgasi
            para_birimi = kayit.para_birimi

        elif isinstance(
            kayit,
            DovizKaydi,
        ):
            varlik_turu = VarlikTuru.DOVIZ
            fiyat = kayit.orta_fiyat
            alis = kayit.alis_fiyati
            satis = kayit.satis_fiyati
            hacim = None
            degisim = None
            zaman = kayit.zaman_damgasi
            para_birimi = kayit.para_birimi

        elif isinstance(
            kayit,
            KiymetliMadenKaydi,
        ):
            varlik_turu = (
                VarlikTuru.ALTIN
                if kayit.kod == "ALTIN"
                else VarlikTuru.GUMUS
            )
            fiyat = kayit.orta_fiyat
            alis = kayit.alis_fiyati
            satis = kayit.satis_fiyati
            hacim = None
            degisim = None
            zaman = kayit.zaman_damgasi
            para_birimi = kayit.para_birimi

        else:
            raise TypeError(
                "Desteklenmeyen kaynak kaydı."
            )

        veri = PiyasaVerisi(
            sembol=anahtar,
            varlik_turu=varlik_turu,
            fiyat=_ondalik(fiyat),
            para_birimi=para_birimi,
            zaman_damgasi=(
                _zaman_dogrula(zaman)
            ),
            kaynak=(
                f"{self.saglayici_id} "
                f"{self.kaynak_sinifi.value}"
            ),
            saglayici_id=(
                self.saglayici_id
            ),
            veri_durumu=(
                self.veri_durumu
            ),
            gecikme_saniyesi=(
                self.gecikme_saniyesi
            ),
            alis_fiyati=(
                _ondalik(alis)
                if alis is not None
                else None
            ),
            satis_fiyati=(
                _ondalik(satis)
                if satis is not None
                else None
            ),
            hacim=(
                _ondalik(hacim)
                if hacim is not None
                else None
            ),
            degisim_orani=degisim,
            dogrulandi=True,
        )

        muhurlu = (
            VeriDogruLamaMotoru
            .muhurle(veri)
        )

        return KaynakliPiyasaVerisi(
            veri=muhurlu,
            guven_profili=(
                self.guven_profili
            ),
        )


class KapBildirimDogrulamaMotoru:
    @classmethod
    def muhurle(
        cls,
        bildirim: KapBildirimi,
    ) -> KapBildirimi:
        kanit = {
            "bildirim_id": (
                bildirim.bildirim_id
            ),
            "sembol": bildirim.sembol,
            "baslik": bildirim.baslik,
            "yayin_zamani": (
                bildirim.yayin_zamani
            ),
            "bildirim_turu": (
                bildirim.bildirim_turu
            ),
            "ozet": bildirim.ozet,
            "kaynak_adresi": (
                bildirim.kaynak_adresi
            ),
            "onem": bildirim.onem.value,
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return replace(
            bildirim,
            dogrulanmis=True,
            bildirim_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    @classmethod
    def dogrula(
        cls,
        bildirim: KapBildirimi,
    ) -> bool:
        if not (
            bildirim.dogrulanmis
            and bildirim.bildirim_sha256
        ):
            return False

        yeniden = cls.muhurle(
            KapBildirimi(
                bildirim_id=(
                    bildirim.bildirim_id
                ),
                sembol=bildirim.sembol,
                baslik=bildirim.baslik,
                yayin_zamani=(
                    bildirim.yayin_zamani
                ),
                bildirim_turu=(
                    bildirim.bildirim_turu
                ),
                ozet=bildirim.ozet,
                kaynak_adresi=(
                    bildirim.kaynak_adresi
                ),
                onem=bildirim.onem,
            )
        )

        return (
            yeniden.bildirim_sha256
            == bildirim.bildirim_sha256
        )


class FinansKaynakHavuzu:
    def __init__(
        self,
        *,
        bagdastiricilar: Iterable[
            PiyasaKaynakBagdastiricisi
        ],
    ) -> None:
        self.bagdastiricilar = tuple(
            bagdastiricilar
        )

        if not self.bagdastiricilar:
            raise ValueError(
                "En az bir finans kaynağı gereklidir."
            )

        kimlikler = [
            kaynak.saglayici_id
            for kaynak
            in self.bagdastiricilar
        ]

        if len(set(kimlikler)) != len(
            kimlikler
        ):
            raise ValueError(
                "Aynı sağlayıcı kimliği "
                "birden fazla kullanılamaz."
            )

    def verileri_getir(
        self,
        *,
        sembol: str,
    ) -> tuple[
        KaynakliPiyasaVerisi,
        ...
    ]:
        sonuclar: list[
            KaynakliPiyasaVerisi
        ] = []

        for kaynak in self.bagdastiricilar:
            try:
                sonuclar.append(
                    kaynak.piyasa_verisi_getir(
                        sembol=sembol
                    )
                )
            except (
                KeyError,
                ConnectionError,
                TimeoutError,
            ):
                continue

        if not sonuclar:
            raise ConnectionError(
                "Hiçbir kaynak geçerli veri üretmedi."
            )

        return tuple(
            sonuclar
        )