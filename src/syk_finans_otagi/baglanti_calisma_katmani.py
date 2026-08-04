from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
import os
from pathlib import Path
from threading import RLock
import time
from typing import Any, Callable, Mapping
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import (
    Request,
    urlopen,
)


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


class KaynakSaglikDurumu(StrEnum):
    SAGLIKLI = "saglikli"
    YAVAS = "yavas"
    KESINTILI = "kesintili"
    ERISILEMIYOR = "erisilemiyor"
    BILINMIYOR = "bilinmiyor"


class YanitKaynagi(StrEnum):
    CANLI = "canli"
    SON_GUVENILIR = "son_guvenilir"
    YEREL_ORNEK = "yerel_ornek"


@dataclass(frozen=True, slots=True)
class BaglantiAyarlari:
    saglayici_id: str
    temel_adres: str
    zaman_asimi_saniyesi: float = 10.0
    yeniden_deneme_sayisi: int = 2
    yeniden_deneme_bekleme_saniyesi: float = 0.25
    asgari_istek_araligi_saniyesi: float = 0.0
    gizli_anahtar_ortam_degikeni: str | None = None
    gizli_anahtar_basligi: str = "Authorization"
    gizli_anahtar_on_eki: str = "Bearer"
    kullanici_aracisi: str = (
        "SyFinansOtigi/1.0"
    )

    def __post_init__(self) -> None:
        if not self.saglayici_id.strip():
            raise ValueError(
                "Sağlayıcı kimliği boş olamaz."
            )

        if not self.temel_adres.strip():
            raise ValueError(
                "Temel adres boş olamaz."
            )

        if self.zaman_asimi_saniyesi <= 0:
            raise ValueError(
                "Zaman aşımı pozitif olmalıdır."
            )

        if self.yeniden_deneme_sayisi < 0:
            raise ValueError(
                "Yeniden deneme sayısı "
                "negatif olamaz."
            )

        if (
            self.asgari_istek_araligi_saniyesi
            < 0
        ):
            raise ValueError(
                "İstek aralığı negatif olamaz."
            )


@dataclass(frozen=True, slots=True)
class KaynakSaglikKaydi:
    saglayici_id: str
    durum: KaynakSaglikDurumu
    basarili_istek_sayisi: int
    basarisiz_istek_sayisi: int
    ardisik_hata_sayisi: int
    son_basarili_zaman: str | None
    son_hata_zamani: str | None
    son_hata: str | None
    son_gecikme_milisaniye: float | None

    @property
    def basari_orani(self) -> float:
        toplam = (
            self.basarili_istek_sayisi
            + self.basarisiz_istek_sayisi
        )

        if toplam <= 0:
            return 0.0

        return round(
            (
                self.basarili_istek_sayisi
                / toplam
                * 100.0
            ),
            3,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "durum": self.durum.value,
            "basarili_istek_sayisi": (
                self.basarili_istek_sayisi
            ),
            "basarisiz_istek_sayisi": (
                self.basarisiz_istek_sayisi
            ),
            "ardisik_hata_sayisi": (
                self.ardisik_hata_sayisi
            ),
            "son_basarili_zaman": (
                self.son_basarili_zaman
            ),
            "son_hata_zamani": (
                self.son_hata_zamani
            ),
            "son_hata": self.son_hata,
            "son_gecikme_milisaniye": (
                self.son_gecikme_milisaniye
            ),
            "basari_orani": (
                self.basari_orani
            ),
        }


@dataclass(frozen=True, slots=True)
class BaglantiYaniti:
    saglayici_id: str
    istek_adresi: str
    durum_kodu: int
    veri: Any
    yanit_kaynagi: YanitKaynagi
    istek_zamani: str
    gecikme_milisaniye: float
    deneme_sayisi: int
    cevrimdisi: bool
    hata: str | None
    yanit_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "istek_adresi": (
                self.istek_adresi
            ),
            "durum_kodu": (
                self.durum_kodu
            ),
            "veri": self.veri,
            "yanit_kaynagi": (
                self.yanit_kaynagi.value
            ),
            "istek_zamani": (
                self.istek_zamani
            ),
            "gecikme_milisaniye": (
                self.gecikme_milisaniye
            ),
            "deneme_sayisi": (
                self.deneme_sayisi
            ),
            "cevrimdisi": (
                self.cevrimdisi
            ),
            "hata": self.hata,
            "yanit_sha256": (
                self.yanit_sha256
            ),
        }


class SonGuvenilirYanitDeposu:
    def __init__(
        self,
        *,
        dosya_yolu: (
            str | Path | None
        ) = None,
    ) -> None:
        self.dosya_yolu = (
            Path(dosya_yolu)
            if dosya_yolu is not None
            else None
        )

        self._yanitlar: dict[
            str,
            dict[str, Any],
        ] = {}

        self._lock = RLock()

        if (
            self.dosya_yolu is not None
            and self.dosya_yolu.is_file()
        ):
            self._yanitlar = json.loads(
                self.dosya_yolu.read_text(
                    encoding="utf-8"
                )
            )

    def kaydet(
        self,
        *,
        anahtar: str,
        veri: Any,
    ) -> None:
        kayit = {
            "veri": veri,
            "kayit_zamani": _simdi(),
        }

        with self._lock:
            self._yanitlar[
                anahtar
            ] = kayit

            if self.dosya_yolu is not None:
                self.dosya_yolu.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                self.dosya_yolu.write_text(
                    json.dumps(
                        self._yanitlar,
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

    def getir(
        self,
        *,
        anahtar: str,
    ) -> Any:
        with self._lock:
            try:
                return self._yanitlar[
                    anahtar
                ]["veri"]
            except KeyError as error:
                raise KeyError(
                    "Son güvenilir yanıt "
                    f"bulunamadı: {anahtar}"
                ) from error

    def var_mi(
        self,
        *,
        anahtar: str,
    ) -> bool:
        with self._lock:
            return (
                anahtar
                in self._yanitlar
            )


class KaynakSaglikIzleyici:
    def __init__(
        self,
        *,
        saglayici_id: str,
    ) -> None:
        self._kayit = KaynakSaglikKaydi(
            saglayici_id=saglayici_id,
            durum=(
                KaynakSaglikDurumu
                .BILINMIYOR
            ),
            basarili_istek_sayisi=0,
            basarisiz_istek_sayisi=0,
            ardisik_hata_sayisi=0,
            son_basarili_zaman=None,
            son_hata_zamani=None,
            son_hata=None,
            son_gecikme_milisaniye=None,
        )

        self._lock = RLock()

    def basari(
        self,
        *,
        gecikme_milisaniye: float,
    ) -> None:
        durum = (
            KaynakSaglikDurumu.YAVAS
            if gecikme_milisaniye >= 2000
            else KaynakSaglikDurumu.SAGLIKLI
        )

        with self._lock:
            self._kayit = replace(
                self._kayit,
                durum=durum,
                basarili_istek_sayisi=(
                    self._kayit
                    .basarili_istek_sayisi
                    + 1
                ),
                ardisik_hata_sayisi=0,
                son_basarili_zaman=_simdi(),
                son_hata=None,
                son_gecikme_milisaniye=round(
                    gecikme_milisaniye,
                    3,
                ),
            )

    def hata(
        self,
        *,
        aciklama: str,
    ) -> None:
        yeni_hata_sayisi = (
            self._kayit
            .ardisik_hata_sayisi
            + 1
        )

        durum = (
            KaynakSaglikDurumu
            .ERISILEMIYOR
            if yeni_hata_sayisi >= 3
            else KaynakSaglikDurumu
            .KESINTILI
        )

        with self._lock:
            self._kayit = replace(
                self._kayit,
                durum=durum,
                basarisiz_istek_sayisi=(
                    self._kayit
                    .basarisiz_istek_sayisi
                    + 1
                ),
                ardisik_hata_sayisi=(
                    yeni_hata_sayisi
                ),
                son_hata_zamani=_simdi(),
                son_hata=str(
                    aciklama
                ),
            )

    def snapshot(
        self,
    ) -> KaynakSaglikKaydi:
        with self._lock:
            return self._kayit


class FinansAgIstemcisi:
    def __init__(
        self,
        *,
        ayarlar: BaglantiAyarlari,
        depo: (
            SonGuvenilirYanitDeposu
            | None
        ) = None,
        yerel_ornekler: (
            Mapping[str, Any] | None
        ) = None,
        tasiyici: (
            Callable[
                [
                    str,
                    Mapping[str, str],
                    float,
                ],
                tuple[
                    int,
                    bytes,
                ],
            ]
            | None
        ) = None,
        uyku: Callable[
            [float],
            None,
        ] = time.sleep,
        saat: Callable[
            [],
            float,
        ] = time.monotonic,
    ) -> None:
        self.ayarlar = ayarlar

        self.depo = (
            depo
            or SonGuvenilirYanitDeposu()
        )

        self.yerel_ornekler = dict(
            yerel_ornekler
            or {}
        )

        self.tasiyici = (
            tasiyici
            or self._gercek_tasiyici
        )

        self.uyku = uyku
        self.saat = saat

        self.saglik = (
            KaynakSaglikIzleyici(
                saglayici_id=(
                    ayarlar.saglayici_id
                )
            )
        )

        self._son_istek_zamani: (
            float | None
        ) = None

        self._lock = RLock()

    @staticmethod
    def _gercek_tasiyici(
        adres: str,
        basliklar: Mapping[str, str],
        zaman_asimi: float,
    ) -> tuple[int, bytes]:
        istek = Request(
            adres,
            headers=dict(
                basliklar
            ),
            method="GET",
        )

        with urlopen(
            istek,
            timeout=zaman_asimi,
        ) as yanit:
            return (
                int(
                    yanit.status
                ),
                yanit.read(),
            )

    def _basliklar(
        self,
    ) -> dict[str, str]:
        basliklar = {
            "Accept": "application/json",
            "User-Agent": (
                self.ayarlar
                .kullanici_aracisi
            ),
        }

        ortam_adi = (
            self.ayarlar
            .gizli_anahtar_ortam_degikeni
        )

        if ortam_adi:
            gizli_anahtar = os.getenv(
                ortam_adi
            )

            if not gizli_anahtar:
                raise RuntimeError(
                    "Gerekli gizli anahtar "
                    f"bulunamadı: {ortam_adi}"
                )

            on_ek = (
                self.ayarlar
                .gizli_anahtar_on_eki
                .strip()
            )

            deger = (
                f"{on_ek} {gizli_anahtar}"
                if on_ek
                else gizli_anahtar
            )

            basliklar[
                self.ayarlar
                .gizli_anahtar_basligi
            ] = deger

        return basliklar

    def _istek_sinirini_bekle(
        self,
    ) -> None:
        with self._lock:
            if (
                self._son_istek_zamani
                is None
            ):
                return

            gecen = (
                self.saat()
                - self._son_istek_zamani
            )

            kalan = (
                self.ayarlar
                .asgari_istek_araligi_saniyesi
                - gecen
            )

            if kalan > 0:
                self.uyku(
                    kalan
                )

    def _adres(
        self,
        yol: str,
    ) -> str:
        return (
            self.ayarlar
            .temel_adres
            .rstrip("/")
            + "/"
            + str(yol).lstrip("/")
        )

    @staticmethod
    def _muhur(
        kanit: Mapping[str, Any],
    ) -> str:
        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return sha256(
            kodlu
        ).hexdigest()

    def getir(
        self,
        *,
        yol: str,
        depo_anahtari: str | None = None,
        yerel_ornek_anahtari: (
            str | None
        ) = None,
    ) -> BaglantiYaniti:
        adres = self._adres(
            yol
        )

        anahtar = (
            depo_anahtari
            or adres
        )

        hata_mesajlari: list[str] = []
        baslangic = self.saat()
        deneme_sayisi = 0

        try:
            basliklar = self._basliklar()
        except RuntimeError as error:
            self.saglik.hata(
                aciklama=str(error)
            )
            raise

        toplam_deneme = (
            self.ayarlar
            .yeniden_deneme_sayisi
            + 1
        )

        for sira in range(
            toplam_deneme
        ):
            deneme_sayisi = sira + 1

            self._istek_sinirini_bekle()

            istek_baslangici = (
                self.saat()
            )

            try:
                durum_kodu, ham = (
                    self.tasiyici(
                        adres,
                        basliklar,
                        self.ayarlar
                        .zaman_asimi_saniyesi,
                    )
                )

                with self._lock:
                    self._son_istek_zamani = (
                        self.saat()
                    )

                if not (
                    200 <= durum_kodu < 300
                ):
                    raise ConnectionError(
                        "Başarısız durum kodu: "
                        f"{durum_kodu}"
                    )

                veri = json.loads(
                    ham.decode(
                        "utf-8"
                    )
                )

                gecikme = (
                    self.saat()
                    - istek_baslangici
                ) * 1000.0

                self.saglik.basari(
                    gecikme_milisaniye=(
                        gecikme
                    )
                )

                self.depo.kaydet(
                    anahtar=anahtar,
                    veri=veri,
                )

                kanit = {
                    "saglayici_id": (
                        self.ayarlar
                        .saglayici_id
                    ),
                    "adres": adres,
                    "durum_kodu": (
                        durum_kodu
                    ),
                    "veri": veri,
                    "yanit_kaynagi": (
                        YanitKaynagi
                        .CANLI.value
                    ),
                    "deneme_sayisi": (
                        deneme_sayisi
                    ),
                }

                return BaglantiYaniti(
                    saglayici_id=(
                        self.ayarlar
                        .saglayici_id
                    ),
                    istek_adresi=adres,
                    durum_kodu=durum_kodu,
                    veri=veri,
                    yanit_kaynagi=(
                        YanitKaynagi.CANLI
                    ),
                    istek_zamani=_simdi(),
                    gecikme_milisaniye=round(
                        (
                            self.saat()
                            - baslangic
                        )
                        * 1000.0,
                        3,
                    ),
                    deneme_sayisi=(
                        deneme_sayisi
                    ),
                    cevrimdisi=False,
                    hata=None,
                    yanit_sha256=(
                        self._muhur(
                            kanit
                        )
                    ),
                )

            except (
                HTTPError,
                URLError,
                TimeoutError,
                ConnectionError,
                json.JSONDecodeError,
                UnicodeDecodeError,
            ) as error:
                hata_mesajlari.append(
                    str(error)
                )

                self.saglik.hata(
                    aciklama=str(error)
                )

                if (
                    sira
                    < toplam_deneme - 1
                ):
                    self.uyku(
                        self.ayarlar
                        .yeniden_deneme_bekleme_saniyesi
                        * (
                            2 ** sira
                        )
                    )

        hata = " · ".join(
            hata_mesajlari
        )

        if self.depo.var_mi(
            anahtar=anahtar
        ):
            veri = self.depo.getir(
                anahtar=anahtar
            )

            kaynak = (
                YanitKaynagi
                .SON_GUVENILIR
            )

        elif (
            yerel_ornek_anahtari
            and yerel_ornek_anahtari
            in self.yerel_ornekler
        ):
            veri = self.yerel_ornekler[
                yerel_ornek_anahtari
            ]

            kaynak = (
                YanitKaynagi
                .YEREL_ORNEK
            )

        else:
            raise ConnectionError(
                "Canlı bağlantı kurulamadı, "
                "son güvenilir yanıt ve yerel "
                "örnek bulunamadı. "
                + hata
            )

        kanit = {
            "saglayici_id": (
                self.ayarlar
                .saglayici_id
            ),
            "adres": adres,
            "durum_kodu": 0,
            "veri": veri,
            "yanit_kaynagi": (
                kaynak.value
            ),
            "deneme_sayisi": (
                deneme_sayisi
            ),
            "hata": hata,
        }

        return BaglantiYaniti(
            saglayici_id=(
                self.ayarlar
                .saglayici_id
            ),
            istek_adresi=adres,
            durum_kodu=0,
            veri=veri,
            yanit_kaynagi=kaynak,
            istek_zamani=_simdi(),
            gecikme_milisaniye=round(
                (
                    self.saat()
                    - baslangic
                )
                * 1000.0,
                3,
            ),
            deneme_sayisi=(
                deneme_sayisi
            ),
            cevrimdisi=True,
            hata=hata,
            yanit_sha256=(
                self._muhur(
                    kanit
                )
            ),
        )

    def saglik_durumu(
        self,
    ) -> KaynakSaglikKaydi:
        return self.saglik.snapshot()