from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .bist_piyasa_bagdastiricisi import (
    BistPiyasaBagdastiricisi,
)
from .finans_kaynak_merkezi import (
    FinansKaynakMerkezi,
    KaynakMerkeziDurumu,
    MerkeziKapSonucu,
    MerkeziPiyasaSonucu,
)
from .gercek_kaynak_sozlesmeleri import (
    FinansKaynakSinifi,
)
from .kap_bildirim_bagdastiricisi import (
    KapBildirimBagdastiricisi,
)
from .modeller import (
    VarlikTuru,
)
from .tcmb_guvenli_calisma import (
    TcmbGuvenliBagdastiricisi,
)
from .tefas_fon_bagdastiricisi import (
    TefasFonBagdastiricisi,
)


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _varlik_sinifi(
    varlik_turu: VarlikTuru,
) -> FinansKaynakSinifi:
    if (
        varlik_turu
        == VarlikTuru.HISSE
    ):
        return FinansKaynakSinifi.BIST

    if (
        varlik_turu
        == VarlikTuru.FON
    ):
        return FinansKaynakSinifi.FON

    if (
        varlik_turu
        == VarlikTuru.DOVIZ
    ):
        return FinansKaynakSinifi.DOVIZ

    if varlik_turu in {
        VarlikTuru.ALTIN,
        VarlikTuru.GUMUS,
    }:
        return (
            FinansKaynakSinifi
            .KIYMETLI_MADEN
        )

    raise ValueError(
        "Desteklenmeyen varlık türü: "
        f"{varlik_turu.value}"
    )


@dataclass(frozen=True, slots=True)
class OncelikliVarlik:
    sembol: str
    varlik_turu: VarlikTuru
    oncelik: int = 100
    kullanici_etiketi: str = ""

    def __post_init__(self) -> None:
        if not self.sembol.strip():
            raise ValueError(
                "Varlık sembolü boş olamaz."
            )

        if self.oncelik < 0:
            raise ValueError(
                "Varlık önceliği negatif olamaz."
            )

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "sembol": (
                self.sembol
                .strip()
                .upper()
            ),
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "oncelik": self.oncelik,
            "kullanici_etiketi": (
                self.kullanici_etiketi
            ),
        }


@dataclass(frozen=True, slots=True)
class TopluGuncellemeKaydi:
    sembol: str
    varlik_turu: VarlikTuru
    basarili: bool
    fiyat: float | None
    veri_akis_durumu: str | None
    kullanilan_kaynaklar: tuple[
        str,
        ...
    ]
    aciklama: str
    hata: str | None
    sonuc_sha256: str | None

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "basarili": self.basarili,
            "fiyat": self.fiyat,
            "veri_akis_durumu": (
                self.veri_akis_durumu
            ),
            "kullanilan_kaynaklar": list(
                self.kullanilan_kaynaklar
            ),
            "aciklama": self.aciklama,
            "hata": self.hata,
            "sonuc_sha256": (
                self.sonuc_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class TopluGuncellemeSonucu:
    baslangic_zamani: str
    bitis_zamani: str
    toplam_varlik: int
    basarili_varlik: int
    basarisiz_varlik: int
    kayitlar: tuple[
        TopluGuncellemeKaydi,
        ...
    ]
    kaynak_merkezi_snapshot: Mapping[
        str,
        Any,
    ]
    toplu_sha256: str

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "baslangic_zamani": (
                self.baslangic_zamani
            ),
            "bitis_zamani": (
                self.bitis_zamani
            ),
            "toplam_varlik": (
                self.toplam_varlik
            ),
            "basarili_varlik": (
                self.basarili_varlik
            ),
            "basarisiz_varlik": (
                self.basarisiz_varlik
            ),
            "kayitlar": [
                kayit.as_dict()
                for kayit in self.kayitlar
            ],
            "kaynak_merkezi_snapshot": dict(
                self.kaynak_merkezi_snapshot
            ),
            "toplu_sha256": (
                self.toplu_sha256
            ),
        }


class SyFinansCalismaProfili:
    def __init__(
        self,
        *,
        merkez: FinansKaynakMerkezi,
        oncelikli_varliklar: Iterable[
            OncelikliVarlik
        ] = (),
    ) -> None:
        self.merkez = merkez

        self._oncelikli_varliklar: dict[
            tuple[
                str,
                VarlikTuru,
            ],
            OncelikliVarlik,
        ] = {}

        for varlik in oncelikli_varliklar:
            self.varlik_ekle(
                varlik
            )

    @classmethod
    def varsayilan(
        cls,
        *,
        tcmb: (
            TcmbGuvenliBagdastiricisi
            | None
        ) = None,
        kap: (
            KapBildirimBagdastiricisi
            | None
        ) = None,
        tefas: (
            TefasFonBagdastiricisi
            | None
        ) = None,
        bist: (
            BistPiyasaBagdastiricisi
            | None
        ) = None,
        oncelikli_varliklar: Iterable[
            OncelikliVarlik
        ] = (),
    ) -> SyFinansCalismaProfili:
        piyasa_kaynaklari = [
            kaynak
            for kaynak in (
                tcmb,
                tefas,
                bist,
            )
            if kaynak is not None
        ]

        kap_kaynaklari = [
            kaynak
            for kaynak in (
                kap,
            )
            if kaynak is not None
        ]

        merkez = FinansKaynakMerkezi(
            piyasa_kaynaklari=(
                piyasa_kaynaklari
            ),
            kap_kaynaklari=(
                kap_kaynaklari
            ),
        )

        return cls(
            merkez=merkez,
            oncelikli_varliklar=(
                oncelikli_varliklar
            ),
        )

    def varlik_ekle(
        self,
        varlik: OncelikliVarlik,
    ) -> None:
        anahtar = (
            varlik.sembol
            .strip()
            .upper(),
            varlik.varlik_turu,
        )

        self._oncelikli_varliklar[
            anahtar
        ] = OncelikliVarlik(
            sembol=anahtar[0],
            varlik_turu=(
                varlik.varlik_turu
            ),
            oncelik=varlik.oncelik,
            kullanici_etiketi=(
                varlik.kullanici_etiketi
            ),
        )

    def varlik_sil(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> bool:
        anahtar = (
            str(sembol)
            .strip()
            .upper(),
            varlik_turu,
        )

        return (
            self._oncelikli_varliklar
            .pop(
                anahtar,
                None,
            )
            is not None
        )

    def oncelikli_varliklar(
        self,
    ) -> tuple[
        OncelikliVarlik,
        ...
    ]:
        return tuple(
            sorted(
                self._oncelikli_varliklar
                .values(),
                key=lambda varlik: (
                    -varlik.oncelik,
                    varlik.varlik_turu.value,
                    varlik.sembol,
                ),
            )
        )

    def varlik_verisi_getir(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> MerkeziPiyasaSonucu:
        return (
            self.merkez
            .piyasa_verisi_getir(
                sembol=sembol,
                kaynak_sinifi=(
                    _varlik_sinifi(
                        varlik_turu
                    )
                ),
            )
        )

    def kap_bildirimleri_getir(
        self,
        *,
        sembol: str | None = None,
        limit: int = 50,
    ) -> MerkeziKapSonucu:
        return (
            self.merkez
            .kap_bildirimleri_getir(
                sembol=sembol,
                limit=limit,
            )
        )

    def toplu_guncelle(
        self,
    ) -> TopluGuncellemeSonucu:
        baslangic = _simdi()

        kayitlar: list[
            TopluGuncellemeKaydi
        ] = []

        for varlik in (
            self.oncelikli_varliklar()
        ):
            try:
                sonuc = (
                    self.varlik_verisi_getir(
                        sembol=(
                            varlik.sembol
                        ),
                        varlik_turu=(
                            varlik.varlik_turu
                        ),
                    )
                )

                kayitlar.append(
                    TopluGuncellemeKaydi(
                        sembol=(
                            varlik.sembol
                        ),
                        varlik_turu=(
                            varlik.varlik_turu
                        ),
                        basarili=True,
                        fiyat=float(
                            sonuc.secilen_fiyat
                        ),
                        veri_akis_durumu=(
                            sonuc
                            .veri_akis_durumu
                            .value
                        ),
                        kullanilan_kaynaklar=(
                            sonuc
                            .kullanilan_kaynaklar
                        ),
                        aciklama=(
                            sonuc
                            .kullanici_aciklamasi
                        ),
                        hata=None,
                        sonuc_sha256=(
                            sonuc.merkez_sha256
                        ),
                    )
                )

            except (
                ValueError,
                KeyError,
                ConnectionError,
                TimeoutError,
                RuntimeError,
            ) as error:
                kayitlar.append(
                    TopluGuncellemeKaydi(
                        sembol=(
                            varlik.sembol
                        ),
                        varlik_turu=(
                            varlik.varlik_turu
                        ),
                        basarili=False,
                        fiyat=None,
                        veri_akis_durumu=None,
                        kullanilan_kaynaklar=(),
                        aciklama=(
                            "Varlık güncellenemedi."
                        ),
                        hata=str(
                            error
                        ),
                        sonuc_sha256=None,
                    )
                )

        bitis = _simdi()

        basarili_sayisi = sum(
            kayit.basarili
            for kayit in kayitlar
        )

        snapshot = (
            self.merkez.snapshot()
        )

        kanit = {
            "baslangic_zamani": (
                baslangic
            ),
            "bitis_zamani": bitis,
            "kayitlar": [
                kayit.as_dict()
                for kayit in kayitlar
            ],
            "kaynak_snapshot_sha256": (
                snapshot[
                    "snapshot_sha256"
                ]
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return TopluGuncellemeSonucu(
            baslangic_zamani=(
                baslangic
            ),
            bitis_zamani=bitis,
            toplam_varlik=len(
                kayitlar
            ),
            basarili_varlik=(
                basarili_sayisi
            ),
            basarisiz_varlik=(
                len(
                    kayitlar
                )
                - basarili_sayisi
            ),
            kayitlar=tuple(
                kayitlar
            ),
            kaynak_merkezi_snapshot=(
                snapshot
            ),
            toplu_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

    def kaynak_saglik_ozeti(
        self,
    ) -> dict[str, Any]:
        snapshot = (
            self.merkez.snapshot()
        )

        kaynaklar = snapshot[
            "kaynaklar"
        ]

        return {
            "durum": snapshot["durum"],
            "kaynak_sayisi": (
                snapshot[
                    "kaynak_sayisi"
                ]
            ),
            "hazir_kaynak_sayisi": (
                snapshot[
                    "hazir_kaynak_sayisi"
                ]
            ),
            "hata_kaynagi_sayisi": (
                snapshot[
                    "hata_kaynagi_sayisi"
                ]
            ),
            "kaynaklar": [
                {
                    "saglayici_id": (
                        kaynak[
                            "saglayici_id"
                        ]
                    ),
                    "kaynak_sinifi": (
                        kaynak[
                            "kaynak_sinifi"
                        ]
                    ),
                    "durum": (
                        kaynak["durum"]
                    ),
                    "veri_akis_durumu": (
                        kaynak[
                            "veri_akis_durumu"
                        ]
                    ),
                    "basari_orani": (
                        kaynak[
                            "basari_orani"
                        ]
                    ),
                    "son_hata": (
                        kaynak["son_hata"]
                    ),
                }
                for kaynak in kaynaklar
            ],
            "snapshot_sha256": (
                snapshot[
                    "snapshot_sha256"
                ]
            ),
        }


class KasifFinansGecidi:
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

    def varlik_bilgisi(
        self,
        *,
        sembol: str,
        varlik_turu: VarlikTuru,
    ) -> dict[str, Any]:
        sonuc = (
            self.calisma_profili
            .varlik_verisi_getir(
                sembol=sembol,
                varlik_turu=(
                    varlik_turu
                ),
            )
        )

        return {
            "schema": (
                "syfinans-kasif-gecidi/v1"
            ),
            "sembol": sonuc.sembol,
            "varlik_turu": (
                sonuc.varlik_turu.value
            ),
            "fiyat": float(
                sonuc.secilen_fiyat
            ),
            "veri_akis_durumu": (
                sonuc
                .veri_akis_durumu
                .value
            ),
            "kullanilan_kaynaklar": list(
                sonuc
                .kullanilan_kaynaklar
            ),
            "aciklama": (
                sonuc
                .kullanici_aciklamasi
            ),
            "kanit_sha256": (
                sonuc.merkez_sha256
            ),
            "kesinlik_uyarisi": (
                "Veriler karar desteği içindir; "
                "nihai karar kullanıcıya aittir."
            ),
        }

    def kaynak_durumu(
        self,
    ) -> dict[str, Any]:
        return (
            self.calisma_profili
            .kaynak_saglik_ozeti()
        )