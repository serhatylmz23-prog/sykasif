"""SyKaşif saha cihazı yönetimi ağ yolları."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .eslestirme import (
    SahaCihazAdayi,
    SahaCihazTuru,
    SahaEslestirmeHatasi,
)
from .kesif import SahaKesifHatasi
from .yonetici import (
    SahaCihazBaglantiBilgisi,
    SahaCihazYonetimHatasi,
    SahaCihazYoneticisi,
)


class EslestirmeBaslatmaIstegi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )

    cihaz_kimligi: str = Field(
        alias="cihaz_kimliği",
        min_length=1,
    )
    cihaz_adi: str = Field(
        alias="cihaz_adı",
        min_length=1,
    )
    cihaz_turu: SahaCihazTuru = Field(
        alias="cihaz_türü"
    )
    cihaz_parmak_izi: str = Field(
        alias="cihaz_parmak_izi",
        min_length=1,
    )
    yerel_ag_adresi: str | None = Field(
        default=None,
        alias="yerel_ağ_adresi",
    )
    uygulama_surumu: str | None = Field(
        default=None,
        alias="uygulama_sürümü",
    )
    sistem_surumu: str | None = Field(
        default=None,
        alias="sistem_sürümü",
    )
    yetenekler: list[str] = Field(
        default_factory=list
    )


class EslestirmeOnayIstegi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )

    onaylayan: str = Field(
        min_length=1
    )


class EslestirmeTamamlamaIstegi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )

    kod: str = Field(
        min_length=6,
        max_length=6,
    )
    cihaz_kimligi: str = Field(
        alias="cihaz_kimliği",
        min_length=1,
    )
    cihaz_parmak_izi: str = Field(
        alias="cihaz_parmak_izi",
        min_length=1,
    )
    ag_adresi: str = Field(
        alias="ağ_adresi",
        min_length=1,
    )
    hizmet_noktasi: int = Field(
        alias="hizmet_noktası",
        ge=1,
        le=65535,
    )


class YenidenBaglanmaIstegi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )

    cihaz_kimligi: str = Field(
        alias="cihaz_kimliği",
        min_length=1,
    )
    cihaz_parmak_izi: str = Field(
        alias="cihaz_parmak_izi",
        min_length=1,
    )
    oturum_anahtari: str = Field(
        alias="oturum_anahtarı",
        min_length=1,
    )
    ag_adresi: str = Field(
        alias="ağ_adresi",
        min_length=1,
    )
    hizmet_noktasi: int = Field(
        alias="hizmet_noktası",
        ge=1,
        le=65535,
    )


class SahaCihazAgGecidi:
    """Birleşik saha cihazı yöneticisini ağ yollarına bağlar."""

    def __init__(
        self,
        yonetici: SahaCihazYoneticisi,
        *,
        uygulama: FastAPI | None = None,
        kok_yol: str = "/saha-cihazlari",
    ) -> None:
        if not kok_yol.startswith("/"):
            raise ValueError(
                "Kök yol eğik çizgiyle başlamalıdır."
            )

        self.yonetici = yonetici
        self.kok_yol = kok_yol.rstrip("/")

        self.uygulama = (
            uygulama
            or FastAPI(
                title="SyKaşif Saha Cihazları",
                version="0.1.0",
            )
        )

        self._yollari_kaydet()

        self.uygulama.state.saha_cihaz_ag_gecidi = (
            self
        )

    def _yollari_kaydet(self) -> None:
        @self.uygulama.get(
            f"{self.kok_yol}/saglik"
        )
        async def saglik() -> dict[str, Any]:
            return {
                "başarılı": True,
                "durum": "sağlıklı",
                "bileşen": "saha_cihaz_yönetimi",
            }

        @self.uygulama.get(
            f"{self.kok_yol}/durum"
        )
        async def durum() -> dict[str, Any]:
            return {
                "başarılı": True,
                "durum": (
                    self.yonetici.durum_ozeti()
                ),
            }

        @self.uygulama.post(
            f"{self.kok_yol}/eslestirme",
            status_code=201,
        )
        async def eslestirme_baslat(
            istek: EslestirmeBaslatmaIstegi,
        ) -> dict[str, Any]:
            try:
                cihaz = SahaCihazAdayi(
                    cihaz_kimligi=(
                        istek.cihaz_kimligi
                    ),
                    cihaz_adi=istek.cihaz_adi,
                    cihaz_turu=istek.cihaz_turu,
                    cihaz_parmak_izi=(
                        istek.cihaz_parmak_izi
                    ),
                    yerel_ag_adresi=(
                        istek.yerel_ag_adresi
                    ),
                    uygulama_surumu=(
                        istek.uygulama_surumu
                    ),
                    sistem_surumu=(
                        istek.sistem_surumu
                    ),
                    yetenekler=frozenset(
                        istek.yetenekler
                    ),
                )

                eslestirme, kod = (
                    self.yonetici
                    .eslestirme_baslat(cihaz)
                )

                return {
                    "başarılı": True,
                    "eşleştirme": (
                        eslestirme.sozluk()
                    ),
                    "tek_kullanımlık_kod": kod,
                }

            except (
                ValueError,
                SahaEslestirmeHatasi,
            ) as hata:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

        @self.uygulama.post(
            f"{self.kok_yol}/eslestirme/"
            "{istek_kimligi}/onayla"
        )
        async def eslestirme_onayla(
            istek_kimligi: str,
            istek: EslestirmeOnayIstegi,
        ) -> dict[str, Any]:
            try:
                sonuc = (
                    self.yonetici
                    .eslestirmeyi_onayla(
                        istek_kimligi,
                        onaylayan=(
                            istek.onaylayan
                        ),
                    )
                )

                return {
                    "başarılı": True,
                    "eşleştirme": sonuc.sozluk(),
                }

            except SahaEslestirmeHatasi as hata:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

        @self.uygulama.post(
            f"{self.kok_yol}/eslestirme/"
            "{istek_kimligi}/tamamla"
        )
        async def eslestirme_tamamla(
            istek_kimligi: str,
            istek: EslestirmeTamamlamaIstegi,
        ) -> dict[str, Any]:
            try:
                eslestirme, cihaz = (
                    self.yonetici
                    .eslestirmeyi_tamamla(
                        istek_kimligi,
                        kod=istek.kod,
                        baglanti=(
                            SahaCihazBaglantiBilgisi(
                                cihaz_kimligi=(
                                    istek
                                    .cihaz_kimligi
                                ),
                                cihaz_parmak_izi=(
                                    istek
                                    .cihaz_parmak_izi
                                ),
                                ag_adresi=(
                                    istek.ag_adresi
                                ),
                                hizmet_noktasi=(
                                    istek
                                    .hizmet_noktasi
                                ),
                            )
                        ),
                    )
                )

                return {
                    "başarılı": True,
                    "eşleştirme": (
                        eslestirme.sozluk()
                    ),
                    "cihaz": cihaz.sozluk(),
                    "oturum_anahtarı": (
                        eslestirme
                        .oturum_anahtari
                    ),
                }

            except (
                SahaEslestirmeHatasi,
                SahaKesifHatasi,
                SahaCihazYonetimHatasi,
            ) as hata:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

        @self.uygulama.post(
            f"{self.kok_yol}/yeniden-baglan"
        )
        async def yeniden_baglan(
            istek: YenidenBaglanmaIstegi,
        ) -> dict[str, Any]:
            try:
                cihaz = (
                    self.yonetici
                    .yeniden_baglan(
                        baglanti=(
                            SahaCihazBaglantiBilgisi(
                                cihaz_kimligi=(
                                    istek
                                    .cihaz_kimligi
                                ),
                                cihaz_parmak_izi=(
                                    istek
                                    .cihaz_parmak_izi
                                ),
                                ag_adresi=(
                                    istek.ag_adresi
                                ),
                                hizmet_noktasi=(
                                    istek
                                    .hizmet_noktasi
                                ),
                            )
                        ),
                        oturum_anahtari=(
                            istek.oturum_anahtari
                        ),
                    )
                )

                return {
                    "başarılı": True,
                    "cihaz": cihaz.sozluk(),
                }

            except (
                SahaKesifHatasi,
                SahaCihazYonetimHatasi,
            ) as hata:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

        @self.uygulama.post(
            f"{self.kok_yol}/zaman-asimi-kontrolu"
        )
        async def zaman_asimi_kontrolu(
        ) -> dict[str, Any]:
            cihazlar = (
                self.yonetici
                .zaman_asimlarini_kontrol_et()
            )

            return {
                "başarılı": True,
                "değişen_cihaz_sayısı": (
                    len(cihazlar)
                ),
                "cihazlar": [
                    cihaz.sozluk()
                    for cihaz in cihazlar
                ],
            }


def saha_cihaz_ag_gecidini_bagla(
    uygulama: FastAPI,
    yonetici: SahaCihazYoneticisi,
    *,
    kok_yol: str = "/saha-cihazlari",
) -> SahaCihazAgGecidi:
    return SahaCihazAgGecidi(
        yonetici,
        uygulama=uygulama,
        kok_yol=kok_yol,
    )
