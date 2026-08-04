from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Iterable, Protocol

from .baglanti_calisma_katmani import (
    YanitKaynagi,
)
from .capraz_dogrulama import (
    CaprazDogrulamaMotoru,
    CaprazDogrulamaSonucu,
    KaynakliPiyasaVerisi,
)
from .gercek_kaynak_sozlesmeleri import (
    FinansKaynakSinifi,
    KapBildirimi,
)
from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


class KaynakMerkeziDurumu(StrEnum):
    HAZIR = "hazir"
    KISMEN_HAZIR = "kismen_hazir"
    ERISILEMIYOR = "erisilemiyor"
    TANIMSIZ = "tanimsiz"


class PiyasaKaynakSozlesmesi(
    Protocol
):
    @property
    def saglayici_id(
        self,
    ) -> str:
        ...

    @property
    def kaynak_sinifi(
        self,
    ) -> FinansKaynakSinifi:
        ...

    def piyasa_verisi_getir(
        self,
        *,
        sembol: str,
    ) -> KaynakliPiyasaVerisi:
        ...


class KapKaynakSozlesmesi(
    Protocol
):
    @property
    def saglayici_id(
        self,
    ) -> str:
        ...

    def bildirimleri_getir(
        self,
        *,
        sembol: str | None = None,
        limit: int = 50,
    ) -> tuple[
        KapBildirimi,
        ...
    ]:
        ...


@dataclass(frozen=True, slots=True)
class KaynakDurumKaydi:
    saglayici_id: str
    kaynak_sinifi: str
    durum: KaynakMerkeziDurumu
    son_denetim_zamani: str
    son_basarili_zaman: str | None
    son_hata_zamani: str | None
    son_hata: str | None
    veri_akis_durumu: str | None
    yanit_kaynagi: str | None
    toplam_istek: int
    basarili_istek: int
    basarisiz_istek: int

    @property
    def basari_orani(
        self,
    ) -> float:
        if self.toplam_istek <= 0:
            return 0.0

        return round(
            (
                self.basarili_istek
                / self.toplam_istek
                * 100.0
            ),
            3,
        )

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "kaynak_sinifi": (
                self.kaynak_sinifi
            ),
            "durum": self.durum.value,
            "son_denetim_zamani": (
                self.son_denetim_zamani
            ),
            "son_basarili_zaman": (
                self.son_basarili_zaman
            ),
            "son_hata_zamani": (
                self.son_hata_zamani
            ),
            "son_hata": self.son_hata,
            "veri_akis_durumu": (
                self.veri_akis_durumu
            ),
            "yanit_kaynagi": (
                self.yanit_kaynagi
            ),
            "toplam_istek": (
                self.toplam_istek
            ),
            "basarili_istek": (
                self.basarili_istek
            ),
            "basarisiz_istek": (
                self.basarisiz_istek
            ),
            "basari_orani": (
                self.basari_orani
            ),
        }


@dataclass(frozen=True, slots=True)
class MerkeziPiyasaSonucu:
    sembol: str
    varlik_turu: VarlikTuru
    veriler: tuple[
        KaynakliPiyasaVerisi,
        ...
    ]
    capraz_dogrulama: (
        CaprazDogrulamaSonucu
        | None
    )
    kullanilan_kaynaklar: tuple[
        str,
        ...
    ]
    basarisiz_kaynaklar: tuple[
        str,
        ...
    ]
    veri_akis_durumu: VeriAkisDurumu
    kullanici_aciklamasi: str
    merkez_sha256: str

    @property
    def secilen_fiyat(
        self,
    ):
        if (
            self.capraz_dogrulama
            is not None
            and self.capraz_dogrulama
            .uzlasma_fiyati
            is not None
        ):
            return (
                self.capraz_dogrulama
                .uzlasma_fiyati
            )

        return self.veriler[
            0
        ].veri.fiyat

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "secilen_fiyat": float(
                self.secilen_fiyat
            ),
            "veriler": [
                kayit.as_dict()
                for kayit in self.veriler
            ],
            "capraz_dogrulama": (
                self.capraz_dogrulama
                .as_dict()
                if self.capraz_dogrulama
                is not None
                else None
            ),
            "kullanilan_kaynaklar": list(
                self.kullanilan_kaynaklar
            ),
            "basarisiz_kaynaklar": list(
                self.basarisiz_kaynaklar
            ),
            "veri_akis_durumu": (
                self.veri_akis_durumu.value
            ),
            "kullanici_aciklamasi": (
                self.kullanici_aciklamasi
            ),
            "merkez_sha256": (
                self.merkez_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class MerkeziKapSonucu:
    sembol: str | None
    bildirimler: tuple[
        KapBildirimi,
        ...
    ]
    kullanilan_kaynaklar: tuple[
        str,
        ...
    ]
    basarisiz_kaynaklar: tuple[
        str,
        ...
    ]
    kullanici_aciklamasi: str
    merkez_sha256: str

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "bildirimler": [
                bildirim.as_dict()
                for bildirim
                in self.bildirimler
            ],
            "bildirim_sayisi": len(
                self.bildirimler
            ),
            "kullanilan_kaynaklar": list(
                self.kullanilan_kaynaklar
            ),
            "basarisiz_kaynaklar": list(
                self.basarisiz_kaynaklar
            ),
            "kullanici_aciklamasi": (
                self.kullanici_aciklamasi
            ),
            "merkez_sha256": (
                self.merkez_sha256
            ),
        }


class FinansKaynakMerkezi:
    def __init__(
        self,
        *,
        piyasa_kaynaklari: Iterable[
            PiyasaKaynakSozlesmesi
        ] = (),
        kap_kaynaklari: Iterable[
            KapKaynakSozlesmesi
        ] = (),
    ) -> None:
        self._piyasa_kaynaklari: dict[
            str,
            PiyasaKaynakSozlesmesi,
        ] = {}

        self._kap_kaynaklari: dict[
            str,
            KapKaynakSozlesmesi,
        ] = {}

        self._durumlar: dict[
            str,
            KaynakDurumKaydi,
        ] = {}

        self._lock = RLock()

        for kaynak in piyasa_kaynaklari:
            self.piyasa_kaynagi_ekle(
                kaynak
            )

        for kaynak in kap_kaynaklari:
            self.kap_kaynagi_ekle(
                kaynak
            )

    def piyasa_kaynagi_ekle(
        self,
        kaynak: PiyasaKaynakSozlesmesi,
    ) -> None:
        kimlik = str(
            kaynak.saglayici_id
        ).strip()

        if not kimlik:
            raise ValueError(
                "Piyasa sağlayıcı kimliği "
                "boş olamaz."
            )

        with self._lock:
            if (
                kimlik
                in self._piyasa_kaynaklari
                or kimlik
                in self._kap_kaynaklari
            ):
                raise ValueError(
                    "Kaynak kimliği daha önce "
                    f"kaydedilmiş: {kimlik}"
                )

            self._piyasa_kaynaklari[
                kimlik
            ] = kaynak

            self._durumlar[
                kimlik
            ] = self._ilk_durum(
                saglayici_id=kimlik,
                kaynak_sinifi=(
                    kaynak
                    .kaynak_sinifi
                    .value
                ),
            )

    def kap_kaynagi_ekle(
        self,
        kaynak: KapKaynakSozlesmesi,
    ) -> None:
        kimlik = str(
            kaynak.saglayici_id
        ).strip()

        if not kimlik:
            raise ValueError(
                "KAP sağlayıcı kimliği "
                "boş olamaz."
            )

        with self._lock:
            if (
                kimlik
                in self._piyasa_kaynaklari
                or kimlik
                in self._kap_kaynaklari
            ):
                raise ValueError(
                    "Kaynak kimliği daha önce "
                    f"kaydedilmiş: {kimlik}"
                )

            self._kap_kaynaklari[
                kimlik
            ] = kaynak

            self._durumlar[
                kimlik
            ] = self._ilk_durum(
                saglayici_id=kimlik,
                kaynak_sinifi=(
                    FinansKaynakSinifi
                    .KAP.value
                ),
            )

    @staticmethod
    def _ilk_durum(
        *,
        saglayici_id: str,
        kaynak_sinifi: str,
    ) -> KaynakDurumKaydi:
        return KaynakDurumKaydi(
            saglayici_id=saglayici_id,
            kaynak_sinifi=(
                kaynak_sinifi
            ),
            durum=(
                KaynakMerkeziDurumu
                .TANIMSIZ
            ),
            son_denetim_zamani=_simdi(),
            son_basarili_zaman=None,
            son_hata_zamani=None,
            son_hata=None,
            veri_akis_durumu=None,
            yanit_kaynagi=None,
            toplam_istek=0,
            basarili_istek=0,
            basarisiz_istek=0,
        )

    def _basari_kaydet(
        self,
        *,
        saglayici_id: str,
        veri_akis_durumu: (
            VeriAkisDurumu
            | None
        ) = None,
        yanit_kaynagi: (
            YanitKaynagi
            | str
            | None
        ) = None,
    ) -> None:
        with self._lock:
            onceki = self._durumlar[
                saglayici_id
            ]

            if isinstance(
                yanit_kaynagi,
                YanitKaynagi,
            ):
                yanit_kaynagi_degeri = (
                    yanit_kaynagi.value
                )
            elif yanit_kaynagi is None:
                yanit_kaynagi_degeri = None
            else:
                yanit_kaynagi_degeri = str(
                    yanit_kaynagi
                )

            self._durumlar[
                saglayici_id
            ] = KaynakDurumKaydi(
                saglayici_id=(
                    onceki.saglayici_id
                ),
                kaynak_sinifi=(
                    onceki.kaynak_sinifi
                ),
                durum=(
                    KaynakMerkeziDurumu.HAZIR
                ),
                son_denetim_zamani=_simdi(),
                son_basarili_zaman=_simdi(),
                son_hata_zamani=(
                    onceki.son_hata_zamani
                ),
                son_hata=None,
                veri_akis_durumu=(
                    veri_akis_durumu.value
                    if veri_akis_durumu
                    is not None
                    else None
                ),
                yanit_kaynagi=(
                    yanit_kaynagi_degeri
                ),
                toplam_istek=(
                    onceki.toplam_istek
                    + 1
                ),
                basarili_istek=(
                    onceki.basarili_istek
                    + 1
                ),
                basarisiz_istek=(
                    onceki.basarisiz_istek
                ),
            )

    def _hata_kaydet(
        self,
        *,
        saglayici_id: str,
        hata: Exception,
    ) -> None:
        with self._lock:
            onceki = self._durumlar[
                saglayici_id
            ]

            self._durumlar[
                saglayici_id
            ] = KaynakDurumKaydi(
                saglayici_id=(
                    onceki.saglayici_id
                ),
                kaynak_sinifi=(
                    onceki.kaynak_sinifi
                ),
                durum=(
                    KaynakMerkeziDurumu
                    .ERISILEMIYOR
                ),
                son_denetim_zamani=_simdi(),
                son_basarili_zaman=(
                    onceki.son_basarili_zaman
                ),
                son_hata_zamani=_simdi(),
                son_hata=str(
                    hata
                ),
                veri_akis_durumu=(
                    onceki.veri_akis_durumu
                ),
                yanit_kaynagi=(
                    onceki.yanit_kaynagi
                ),
                toplam_istek=(
                    onceki.toplam_istek
                    + 1
                ),
                basarili_istek=(
                    onceki.basarili_istek
                ),
                basarisiz_istek=(
                    onceki.basarisiz_istek
                    + 1
                ),
            )

    @staticmethod
    def _akis_durumu_belirle(
        veriler: Iterable[
            KaynakliPiyasaVerisi
        ],
    ) -> VeriAkisDurumu:
        durumlar = {
            kayit.veri.veri_durumu
            for kayit in veriler
        }

        if (
            VeriAkisDurumu.CEVRIMDISI
            in durumlar
        ):
            return (
                VeriAkisDurumu.CEVRIMDISI
            )

        if (
            VeriAkisDurumu.GECIKMELI
            in durumlar
        ):
            return (
                VeriAkisDurumu.GECIKMELI
            )

        return VeriAkisDurumu.ANLIK

    def piyasa_verisi_getir(
        self,
        *,
        sembol: str,
        kaynak_sinifi: (
            FinansKaynakSinifi
            | None
        ) = None,
        saglayici_kimlikleri: (
            Iterable[str]
            | None
        ) = None,
    ) -> MerkeziPiyasaSonucu:
        aranan = str(
            sembol
        ).strip().upper()

        if not aranan:
            raise ValueError(
                "Sembol boş olamaz."
            )

        secili_kimlikler = (
            {
                str(kimlik).strip()
                for kimlik
                in saglayici_kimlikleri
            }
            if saglayici_kimlikleri
            is not None
            else None
        )

        with self._lock:
            kaynaklar = tuple(
                self._piyasa_kaynaklari
                .values()
            )

        veriler: list[
            KaynakliPiyasaVerisi
        ] = []

        kullanilanlar: list[str] = []
        basarisizlar: list[str] = []

        for kaynak in kaynaklar:
            kimlik = kaynak.saglayici_id

            if (
                secili_kimlikler
                is not None
                and kimlik
                not in secili_kimlikler
            ):
                continue

            if (
                kaynak_sinifi
                is not None
                and kaynak.kaynak_sinifi
                != kaynak_sinifi
            ):
                continue

            try:
                sonuc = (
                    kaynak
                    .piyasa_verisi_getir(
                        sembol=aranan
                    )
                )

                veriler.append(
                    sonuc
                )

                kullanilanlar.append(
                    kimlik
                )

                self._basari_kaydet(
                    saglayici_id=kimlik,
                    veri_akis_durumu=(
                        sonuc.veri
                        .veri_durumu
                    ),
                )

            except (
                KeyError,
                ValueError,
                ConnectionError,
                TimeoutError,
                RuntimeError,
            ) as error:
                basarisizlar.append(
                    kimlik
                )

                self._hata_kaydet(
                    saglayici_id=kimlik,
                    hata=error,
                )

        if not veriler:
            raise ConnectionError(
                "Hiçbir finans kaynağı "
                f"{aranan} için geçerli veri "
                "üretemedi."
            )

        varlik_turu = (
            veriler[0]
            .veri
            .varlik_turu
        )

        for kayit in veriler:
            if (
                kayit.veri.varlik_turu
                != varlik_turu
            ):
                raise ValueError(
                    "Aynı sembol için farklı "
                    "varlık türleri döndürüldü."
                )

        capraz_sonuc = None

        if len(
            veriler
        ) >= 2:
            capraz_sonuc = (
                CaprazDogrulamaMotoru
                .dogrula(
                    veriler=veriler,
                )
            )

        akis_durumu = (
            self._akis_durumu_belirle(
                veriler
            )
        )

        if (
            capraz_sonuc is not None
            and capraz_sonuc
            .kabul_edilen_kaynak_sayisi
            >= 2
        ):
            aciklama = (
                "Finans verisi birden fazla "
                "kaynaktan karşılaştırılarak "
                "sunuldu."
            )

        elif (
            akis_durumu
            == VeriAkisDurumu.CEVRIMDISI
        ):
            aciklama = (
                "Canlı bağlantı kullanılamıyor; "
                "son güvenilir finans kaydı "
                "gösteriliyor."
            )

        elif (
            akis_durumu
            == VeriAkisDurumu.GECIKMELI
        ):
            aciklama = (
                "Finans verisi gecikmeli "
                "kaynak üzerinden sunuluyor."
            )

        else:
            aciklama = (
                "Finans verisi kullanılabilir "
                "kaynaktan alındı."
            )

        kanit = {
            "sembol": aranan,
            "varlik_turu": (
                varlik_turu.value
            ),
            "kullanilan_kaynaklar": sorted(
                kullanilanlar
            ),
            "basarisiz_kaynaklar": sorted(
                basarisizlar
            ),
            "veri_akis_durumu": (
                akis_durumu.value
            ),
            "veri_sha256": [
                kayit.veri.veri_sha256
                for kayit in veriler
            ],
            "capraz_dogrulama_sha256": (
                capraz_sonuc
                .dogrulama_sha256
                if capraz_sonuc
                is not None
                else None
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return MerkeziPiyasaSonucu(
            sembol=aranan,
            varlik_turu=varlik_turu,
            veriler=tuple(
                veriler
            ),
            capraz_dogrulama=(
                capraz_sonuc
            ),
            kullanilan_kaynaklar=tuple(
                sorted(
                    kullanilanlar
                )
            ),
            basarisiz_kaynaklar=tuple(
                sorted(
                    basarisizlar
                )
            ),
            veri_akis_durumu=(
                akis_durumu
            ),
            kullanici_aciklamasi=(
                aciklama
            ),
            merkez_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    def kap_bildirimleri_getir(
        self,
        *,
        sembol: str | None = None,
        limit: int = 50,
    ) -> MerkeziKapSonucu:
        aranan = (
            str(sembol)
            .strip()
            .upper()
            if sembol
            else None
        )

        with self._lock:
            kaynaklar = tuple(
                self._kap_kaynaklari
                .values()
            )

        bildirimler: list[
            KapBildirimi
        ] = []

        kullanilanlar: list[str] = []
        basarisizlar: list[str] = []

        for kaynak in kaynaklar:
            kimlik = kaynak.saglayici_id

            try:
                gelenler = (
                    kaynak
                    .bildirimleri_getir(
                        sembol=aranan,
                        limit=limit,
                    )
                )

                bildirimler.extend(
                    gelenler
                )

                kullanilanlar.append(
                    kimlik
                )

                self._basari_kaydet(
                    saglayici_id=kimlik,
                )

            except (
                ValueError,
                ConnectionError,
                TimeoutError,
                RuntimeError,
            ) as error:
                basarisizlar.append(
                    kimlik
                )

                self._hata_kaydet(
                    saglayici_id=kimlik,
                    hata=error,
                )

        if not bildirimler:
            raise ConnectionError(
                "Hiçbir KAP kaynağı "
                "kullanılabilir bildirim "
                "üretemedi."
            )

        benzersiz = {
            bildirim.bildirim_id: bildirim
            for bildirim in bildirimler
        }

        sirali = tuple(
            sorted(
                benzersiz.values(),
                key=lambda bildirim: (
                    bildirim.yayin_zamani,
                    bildirim.bildirim_id,
                ),
                reverse=True,
            )[
                :max(
                    1,
                    int(limit),
                )
            ]
        )

        kanit = {
            "sembol": aranan,
            "bildirimler": [
                bildirim.bildirim_sha256
                for bildirim in sirali
            ],
            "kullanilan_kaynaklar": sorted(
                kullanilanlar
            ),
            "basarisiz_kaynaklar": sorted(
                basarisizlar
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return MerkeziKapSonucu(
            sembol=aranan,
            bildirimler=sirali,
            kullanilan_kaynaklar=tuple(
                sorted(
                    kullanilanlar
                )
            ),
            basarisiz_kaynaklar=tuple(
                sorted(
                    basarisizlar
                )
            ),
            kullanici_aciklamasi=(
                "KAP bildirimleri merkezî "
                "kaynak yönetimi üzerinden "
                "sunuldu."
            ),
            merkez_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    def kaynak_durumlari(
        self,
    ) -> tuple[
        KaynakDurumKaydi,
        ...
    ]:
        with self._lock:
            return tuple(
                sorted(
                    self._durumlar.values(),
                    key=lambda kayit: (
                        kayit.kaynak_sinifi,
                        kayit.saglayici_id,
                    ),
                )
            )

    def kaynak_durumu_getir(
        self,
        saglayici_id: str,
    ) -> KaynakDurumKaydi:
        with self._lock:
            try:
                return self._durumlar[
                    saglayici_id
                ]
            except KeyError as error:
                raise KeyError(
                    "Finans kaynağı "
                    "bulunamadı: "
                    f"{saglayici_id}"
                ) from error

    def snapshot(
        self,
    ) -> dict[str, Any]:
        durumlar = self.kaynak_durumlari()

        hazir_sayisi = sum(
            kayit.durum
            == KaynakMerkeziDurumu.HAZIR
            for kayit in durumlar
        )

        hata_sayisi = sum(
            kayit.durum
            == KaynakMerkeziDurumu
            .ERISILEMIYOR
            for kayit in durumlar
        )

        if (
            durumlar
            and hazir_sayisi
            == len(durumlar)
        ):
            merkez_durumu = (
                KaynakMerkeziDurumu.HAZIR
            )

        elif hazir_sayisi > 0:
            merkez_durumu = (
                KaynakMerkeziDurumu
                .KISMEN_HAZIR
            )

        elif hata_sayisi > 0:
            merkez_durumu = (
                KaynakMerkeziDurumu
                .ERISILEMIYOR
            )

        else:
            merkez_durumu = (
                KaynakMerkeziDurumu
                .TANIMSIZ
            )

        kayit = {
            "schema": (
                "syfinans-kaynak-merkezi/v1"
            ),
            "durum": (
                merkez_durumu.value
            ),
            "kaynak_sayisi": len(
                durumlar
            ),
            "hazir_kaynak_sayisi": (
                hazir_sayisi
            ),
            "hata_kaynagi_sayisi": (
                hata_sayisi
            ),
            "kaynaklar": [
                durum.as_dict()
                for durum in durumlar
            ],
        }

        kodlu = json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return {
            **kayit,
            "snapshot_sha256": sha256(
                kodlu
            ).hexdigest(),
        }