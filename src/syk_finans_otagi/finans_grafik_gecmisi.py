from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from typing import Any, Iterable, Mapping


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _zaman(
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


def _ondalik(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


class GrafikDonemi(StrEnum):
    GUNLUK = "gunluk"
    HAFTALIK = "haftalik"
    AYLIK = "aylik"
    TUMU = "tumu"


@dataclass(frozen=True, slots=True)
class FiyatGecmisKaydi:
    sembol: str
    zaman: str
    fiyat: Decimal
    hacim: Decimal | None
    kaynak: str
    veri_sha256: str

    def __post_init__(self) -> None:
        if not self.sembol.strip():
            raise ValueError(
                "Sembol boş olamaz."
            )

        if self.fiyat <= 0:
            raise ValueError(
                "Fiyat pozitif olmalıdır."
            )

        _zaman(
            self.zaman
        )

        if (
            self.hacim is not None
            and self.hacim < 0
        ):
            raise ValueError(
                "Hacim negatif olamaz."
            )

        if len(
            self.veri_sha256
        ) != 64:
            raise ValueError(
                "Geçerli SHA-256 kaydı gereklidir."
            )

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "zaman": self.zaman,
            "fiyat": float(
                self.fiyat
            ),
            "hacim": (
                float(self.hacim)
                if self.hacim is not None
                else None
            ),
            "kaynak": self.kaynak,
            "veri_sha256": (
                self.veri_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class GrafikNoktasi:
    zaman: str
    fiyat: Decimal
    hacim: Decimal | None
    maliyet_cizgisi: Decimal | None
    kar_zarar: Decimal | None

    def as_dict(
        self,
    ) -> dict[str, Any]:
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
            "maliyet_cizgisi": (
                float(self.maliyet_cizgisi)
                if self.maliyet_cizgisi
                is not None
                else None
            ),
            "kar_zarar": (
                float(self.kar_zarar)
                if self.kar_zarar
                is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class GrafikSerisi:
    sembol: str
    donem: GrafikDonemi
    noktalar: tuple[
        GrafikNoktasi,
        ...
    ]
    en_dusuk_fiyat: Decimal
    en_yuksek_fiyat: Decimal
    ilk_fiyat: Decimal
    son_fiyat: Decimal
    degisim_orani: float
    seri_sha256: str

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "schema": (
                "syfinans-grafik-serisi/v1"
            ),
            "sembol": self.sembol,
            "donem": self.donem.value,
            "noktalar": [
                nokta.as_dict()
                for nokta in self.noktalar
            ],
            "en_dusuk_fiyat": float(
                self.en_dusuk_fiyat
            ),
            "en_yuksek_fiyat": float(
                self.en_yuksek_fiyat
            ),
            "ilk_fiyat": float(
                self.ilk_fiyat
            ),
            "son_fiyat": float(
                self.son_fiyat
            ),
            "degisim_orani": (
                self.degisim_orani
            ),
            "seri_sha256": (
                self.seri_sha256
            ),
        }


class FiyatGecmisDeposu:
    def __init__(
        self,
        *,
        dosya_yolu: str | Path | None = None,
    ) -> None:
        self.dosya_yolu = (
            Path(dosya_yolu)
            if dosya_yolu is not None
            else None
        )

        self._kayitlar: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        self._lock = RLock()

        if (
            self.dosya_yolu is not None
            and self.dosya_yolu.is_file()
        ):
            yuklenen = json.loads(
                self.dosya_yolu.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(
                yuklenen,
                Mapping,
            ):
                self._kayitlar = {
                    str(sembol): list(
                        kayitlar
                    )
                    for sembol, kayitlar
                    in yuklenen.items()
                }

    @staticmethod
    def _muhur(
        *,
        sembol: str,
        zaman: str,
        fiyat: Decimal,
        hacim: Decimal | None,
        kaynak: str,
    ) -> str:
        kanit = {
            "sembol": sembol,
            "zaman": zaman,
            "fiyat": str(
                fiyat
            ),
            "hacim": (
                str(hacim)
                if hacim is not None
                else None
            ),
            "kaynak": kaynak,
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

    def kaydet(
        self,
        *,
        sembol: str,
        fiyat: Decimal | int | float | str,
        zaman: str | None = None,
        hacim: (
            Decimal
            | int
            | float
            | str
            | None
        ) = None,
        kaynak: str = "bilinmeyen",
    ) -> FiyatGecmisKaydi:
        sembol_degeri = (
            str(sembol)
            .strip()
            .upper()
        )

        if not sembol_degeri:
            raise ValueError(
                "Sembol boş olamaz."
            )

        fiyat_degeri = _ondalik(
            fiyat
        )

        if fiyat_degeri <= 0:
            raise ValueError(
                "Fiyat pozitif olmalıdır."
            )

        zaman_degeri = _zaman(
            zaman or _simdi()
        )

        hacim_degeri = (
            _ondalik(
                hacim
            )
            if hacim is not None
            else None
        )

        if (
            hacim_degeri is not None
            and hacim_degeri < 0
        ):
            raise ValueError(
                "Hacim negatif olamaz."
            )

        muhur = self._muhur(
            sembol=sembol_degeri,
            zaman=zaman_degeri,
            fiyat=fiyat_degeri,
            hacim=hacim_degeri,
            kaynak=str(
                kaynak
            ),
        )

        kayit = FiyatGecmisKaydi(
            sembol=sembol_degeri,
            zaman=zaman_degeri,
            fiyat=fiyat_degeri,
            hacim=hacim_degeri,
            kaynak=str(
                kaynak
            ),
            veri_sha256=muhur,
        )

        with self._lock:
            liste = self._kayitlar.setdefault(
                sembol_degeri,
                [],
            )

            mevcut = next(
                (
                    oge
                    for oge in liste
                    if oge["zaman"]
                    == zaman_degeri
                ),
                None,
            )

            if mevcut is None:
                liste.append(
                    kayit.as_dict()
                )
            else:
                mevcut.update(
                    kayit.as_dict()
                )

            liste.sort(
                key=lambda oge: oge["zaman"]
            )

            self._diske_yaz()

        return kayit

    def _diske_yaz(
        self,
    ) -> None:
        if self.dosya_yolu is None:
            return

        self.dosya_yolu.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.dosya_yolu.write_text(
            json.dumps(
                self._kayitlar,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def kayitlari_getir(
        self,
        *,
        sembol: str,
    ) -> tuple[
        FiyatGecmisKaydi,
        ...
    ]:
        anahtar = (
            str(sembol)
            .strip()
            .upper()
        )

        with self._lock:
            ham_kayitlar = tuple(
                self._kayitlar.get(
                    anahtar,
                    [],
                )
            )

        return tuple(
            FiyatGecmisKaydi(
                sembol=str(
                    kayit["sembol"]
                ),
                zaman=str(
                    kayit["zaman"]
                ),
                fiyat=_ondalik(
                    kayit["fiyat"]
                ),
                hacim=(
                    _ondalik(
                        kayit["hacim"]
                    )
                    if kayit.get(
                        "hacim"
                    ) is not None
                    else None
                ),
                kaynak=str(
                    kayit["kaynak"]
                ),
                veri_sha256=str(
                    kayit[
                        "veri_sha256"
                    ]
                ),
            )
            for kayit in ham_kayitlar
        )


class FinansGrafikMotoru:
    DONEM_GUNLERI = {
        GrafikDonemi.GUNLUK: 1,
        GrafikDonemi.HAFTALIK: 7,
        GrafikDonemi.AYLIK: 31,
    }

    def __init__(
        self,
        *,
        depo: FiyatGecmisDeposu,
    ) -> None:
        self.depo = depo

    @staticmethod
    def _doneme_gore_filtrele(
        kayitlar: Iterable[
            FiyatGecmisKaydi
        ],
        *,
        donem: GrafikDonemi,
    ) -> tuple[
        FiyatGecmisKaydi,
        ...
    ]:
        sirali = tuple(
            sorted(
                kayitlar,
                key=lambda kayit: (
                    kayit.zaman
                ),
            )
        )

        if (
            not sirali
            or donem
            == GrafikDonemi.TUMU
        ):
            return sirali

        son_zaman = datetime.fromisoformat(
            sirali[-1].zaman
        )

        gun_sayisi = (
            FinansGrafikMotoru
            .DONEM_GUNLERI[
                donem
            ]
        )

        return tuple(
            kayit
            for kayit in sirali
            if (
                son_zaman
                - datetime.fromisoformat(
                    kayit.zaman
                )
            ).total_seconds()
            <= gun_sayisi * 86400
        )

    def seri_uret(
        self,
        *,
        sembol: str,
        donem: GrafikDonemi = (
            GrafikDonemi.TUMU
        ),
        ortalama_maliyet: (
            Decimal
            | int
            | float
            | str
            | None
        ) = None,
        miktar: (
            Decimal
            | int
            | float
            | str
            | None
        ) = None,
    ) -> GrafikSerisi:
        kayitlar = self._doneme_gore_filtrele(
            self.depo.kayitlari_getir(
                sembol=sembol
            ),
            donem=donem,
        )

        if not kayitlar:
            raise ValueError(
                "Grafik üretmek için fiyat "
                "geçmişi bulunamadı."
            )

        maliyet = (
            _ondalik(
                ortalama_maliyet
            )
            if ortalama_maliyet is not None
            else None
        )

        miktar_degeri = (
            _ondalik(
                miktar
            )
            if miktar is not None
            else None
        )

        noktalar: list[
            GrafikNoktasi
        ] = []

        for kayit in kayitlar:
            kar_zarar = None

            if (
                maliyet is not None
                and miktar_degeri is not None
            ):
                kar_zarar = _ondalik(
                    (
                        kayit.fiyat
                        - maliyet
                    )
                    * miktar_degeri
                )

            noktalar.append(
                GrafikNoktasi(
                    zaman=kayit.zaman,
                    fiyat=kayit.fiyat,
                    hacim=kayit.hacim,
                    maliyet_cizgisi=(
                        maliyet
                    ),
                    kar_zarar=(
                        kar_zarar
                    ),
                )
            )

        ilk_fiyat = noktalar[
            0
        ].fiyat

        son_fiyat = noktalar[
            -1
        ].fiyat

        degisim_orani = round(
            float(
                (
                    son_fiyat
                    - ilk_fiyat
                )
                / ilk_fiyat
                * Decimal("100")
            ),
            3,
        )

        kanit = {
            "sembol": (
                str(sembol)
                .strip()
                .upper()
            ),
            "donem": donem.value,
            "noktalar": [
                nokta.as_dict()
                for nokta in noktalar
            ],
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return GrafikSerisi(
            sembol=(
                str(sembol)
                .strip()
                .upper()
            ),
            donem=donem,
            noktalar=tuple(
                noktalar
            ),
            en_dusuk_fiyat=min(
                nokta.fiyat
                for nokta in noktalar
            ),
            en_yuksek_fiyat=max(
                nokta.fiyat
                for nokta in noktalar
            ),
            ilk_fiyat=ilk_fiyat,
            son_fiyat=son_fiyat,
            degisim_orani=(
                degisim_orani
            ),
            seri_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    def ekran_ciktisi(
        self,
        *,
        sembol: str,
        donem: GrafikDonemi = (
            GrafikDonemi.TUMU
        ),
        ortalama_maliyet: (
            Decimal
            | int
            | float
            | str
            | None
        ) = None,
        miktar: (
            Decimal
            | int
            | float
            | str
            | None
        ) = None,
    ) -> dict[str, Any]:
        seri = self.seri_uret(
            sembol=sembol,
            donem=donem,
            ortalama_maliyet=(
                ortalama_maliyet
            ),
            miktar=miktar,
        )

        return {
            "schema": (
                "syfinans-grafik-ekrani/v1"
            ),
            "baslik": (
                f"{seri.sembol} "
                "fiyat geçmişi"
            ),
            "donem": seri.donem.value,
            "fiyat_serisi": [
                {
                    "x": nokta.zaman,
                    "y": float(
                        nokta.fiyat
                    ),
                }
                for nokta in seri.noktalar
            ],
            "hacim_serisi": [
                {
                    "x": nokta.zaman,
                    "y": (
                        float(nokta.hacim)
                        if nokta.hacim
                        is not None
                        else None
                    ),
                }
                for nokta in seri.noktalar
            ],
            "maliyet_serisi": [
                {
                    "x": nokta.zaman,
                    "y": (
                        float(
                            nokta
                            .maliyet_cizgisi
                        )
                        if nokta
                        .maliyet_cizgisi
                        is not None
                        else None
                    ),
                }
                for nokta in seri.noktalar
            ],
            "kar_zarar_serisi": [
                {
                    "x": nokta.zaman,
                    "y": (
                        float(
                            nokta.kar_zarar
                        )
                        if nokta.kar_zarar
                        is not None
                        else None
                    ),
                }
                for nokta in seri.noktalar
            ],
            "ozet": {
                "en_dusuk": float(
                    seri.en_dusuk_fiyat
                ),
                "en_yuksek": float(
                    seri.en_yuksek_fiyat
                ),
                "ilk_fiyat": float(
                    seri.ilk_fiyat
                ),
                "son_fiyat": float(
                    seri.son_fiyat
                ),
                "degisim_orani": (
                    seri.degisim_orani
                ),
            },
            "seri_sha256": (
                seri.seri_sha256
            ),
        }