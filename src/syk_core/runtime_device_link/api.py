"""SyKaşif cihazlar arası iletişim ağ yolları."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .cihaz_yonetici import (
    CihazYonetimHatasi,
    YetkiliCihazYoneticisi,
)
from .guvenlik import (
    GuvenlikHatasi,
    IslemYetkisi,
)


class OturumAcmaIstegi(BaseModel):
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

    gizli_anahtar: str = Field(
        alias="gizli_anahtar",
        min_length=1,
    )

    veri: dict[str, Any] = Field(
        default_factory=dict
    )


class CanlilikIstegi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )

    oturum_kimligi: str = Field(
        alias="oturum_kimliği",
        min_length=1,
    )


class KomutOlusturmaIstegi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )

    oturum_kimligi: str = Field(
        alias="oturum_kimliği",
        min_length=1,
    )

    hedef_cihaz_kimligi: str = Field(
        alias="hedef_cihaz_kimliği",
        min_length=1,
    )

    islem_yetkisi: IslemYetkisi = Field(
        alias="işlem_yetkisi"
    )

    icerik: dict[str, Any] = Field(
        default_factory=dict,
        alias="içerik",
    )

    gerekce: str | None = Field(
        default=None,
        alias="gerekçe",
    )

    insan_onayi: str | None = Field(
        default=None,
        alias="insan_onayı",
    )

    hemen_calistir: bool = Field(
        default=False,
        alias="hemen_çalıştır",
    )


class CihazIletisimAgGecidi:
    """Yetkili cihaz yöneticisini HTTP yollarına bağlar."""

    def __init__(
        self,
        yonetici: YetkiliCihazYoneticisi,
        *,
        uygulama: FastAPI | None = None,
        kok_yol: str = "/cihaz-iletisimi",
    ) -> None:
        if not kok_yol.startswith("/"):
            raise ValueError(
                "Kök yol eğik çizgi ile başlamalıdır."
            )

        self.yonetici = yonetici
        self.uygulama = (
            uygulama
            or FastAPI(
                title="SyKaşif Cihaz İletişimi",
                description=(
                    "Yetkili cihazlar arası güvenli "
                    "iletişim yolları"
                ),
                version="0.1.0",
            )
        )

        self.kok_yol = kok_yol.rstrip("/")

        self._yollari_kaydet()

        self.uygulama.state.cihaz_iletisim_ag_gecidi = (
            self
        )

    def _yollari_kaydet(
        self,
    ) -> None:
        @self.uygulama.get(
            f"{self.kok_yol}/saglik",
            tags=["Cihaz İletişimi"],
        )
        async def saglik() -> dict[str, Any]:
            return {
                "başarılı": True,
                "durum": "sağlıklı",
                "bileşen": (
                    "cihazlar_arası_iletişim"
                ),
            }

        @self.uygulama.get(
            f"{self.kok_yol}/durum",
            tags=["Cihaz İletişimi"],
        )
        async def durum() -> dict[str, Any]:
            return {
                "başarılı": True,
                "durum": (
                    self.yonetici.durum_ozeti()
                ),
            }

        @self.uygulama.get(
            f"{self.kok_yol}/cihazlar",
            tags=["Cihaz İletişimi"],
        )
        async def cihazlar() -> dict[str, Any]:
            return {
                "başarılı": True,
                "cihazlar": [
                    {
                        "cihaz_kimliği": (
                            cihaz.cihaz_kimligi
                        ),
                        "yetki": cihaz.yetki.value,
                        "açıklama": (
                            cihaz.aciklama
                        ),
                    }
                    for cihaz
                    in self.yonetici
                    .cihazlari_listele()
                ],
            }

        @self.uygulama.post(
            f"{self.kok_yol}/oturumlar/ac",
            status_code=201,
            tags=["Cihaz İletişimi"],
        )
        async def oturum_ac(
            istek: OturumAcmaIstegi,
        ) -> dict[str, Any]:
            try:
                oturum = (
                    self.yonetici.oturum_ac(
                        cihaz_kimligi=(
                            istek.cihaz_kimligi
                        ),
                        cihaz_parmak_izi=(
                            istek
                            .cihaz_parmak_izi
                        ),
                        gizli_anahtar=(
                            istek.gizli_anahtar
                        ),
                        veri=dict(
                            istek.veri
                        ),
                    )
                )

                return {
                    "başarılı": True,
                    "oturum": oturum.sozluk(),
                }

            except GuvenlikHatasi as hata:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

            except CihazYonetimHatasi as hata:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

        @self.uygulama.post(
            f"{self.kok_yol}/canlilik",
            tags=["Cihaz İletişimi"],
        )
        async def canlilik(
            istek: CanlilikIstegi,
        ) -> dict[str, Any]:
            try:
                oturum = (
                    self.yonetici
                    .canlilik_bildir(
                        istek.oturum_kimligi
                    )
                )

                return {
                    "başarılı": True,
                    "oturum": oturum.sozluk(),
                }

            except Exception as hata:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

        @self.uygulama.post(
            f"{self.kok_yol}/komutlar",
            status_code=201,
            tags=["Cihaz İletişimi"],
        )
        async def komut_olustur(
            istek: KomutOlusturmaIstegi,
        ) -> dict[str, Any]:
            try:
                komut = (
                    self.yonetici
                    .komut_olustur(
                        oturum_kimligi=(
                            istek.oturum_kimligi
                        ),
                        hedef_cihaz_kimligi=(
                            istek
                            .hedef_cihaz_kimligi
                        ),
                        islem_yetkisi=(
                            istek.islem_yetkisi
                        ),
                        icerik=dict(
                            istek.icerik
                        ),
                        gerekce=(
                            istek.gerekce
                        ),
                        insan_onayi=(
                            istek.insan_onayi
                        ),
                    )
                )

                if istek.hemen_calistir:
                    calistirilan = (
                        self.yonetici
                        .siradaki_komutu_calistir()
                    )

                    if calistirilan is not None:
                        komut = calistirilan

                return {
                    "başarılı": True,
                    "komut": komut.sozluk(),
                }

            except GuvenlikHatasi as hata:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

            except CihazYonetimHatasi as hata:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "başarılı": False,
                        "hata": str(hata),
                    },
                ) from hata

        @self.uygulama.post(
            f"{self.kok_yol}/komutlar/siradakini-calistir",
            tags=["Cihaz İletişimi"],
        )
        async def siradakini_calistir() -> dict[str, Any]:
            komut = (
                self.yonetici
                .siradaki_komutu_calistir()
            )

            return {
                "başarılı": True,
                "komut": (
                    komut.sozluk()
                    if komut is not None
                    else None
                ),
            }

        @self.uygulama.post(
            f"{self.kok_yol}/komutlar/tumunu-calistir",
            tags=["Cihaz İletişimi"],
        )
        async def tumunu_calistir() -> dict[str, Any]:
            komutlar = (
                self.yonetici
                .tum_bekleyenleri_calistir()
            )

            return {
                "başarılı": True,
                "çalıştırılan_komut_sayısı": (
                    len(komutlar)
                ),
                "komutlar": [
                    komut.sozluk()
                    for komut in komutlar
                ],
            }

        @self.uygulama.post(
            f"{self.kok_yol}/zaman-asimlarini-kontrol-et",
            tags=["Cihaz İletişimi"],
        )
        async def zaman_asimlarini_kontrol_et(
        ) -> dict[str, Any]:
            degisenler = (
                self.yonetici
                .zaman_asimlarini_kontrol_et()
            )

            return {
                "başarılı": True,
                "değişen_oturum_sayısı": (
                    len(degisenler)
                ),
                "oturumlar": [
                    oturum.sozluk()
                    for oturum in degisenler
                ],
            }


def cihaz_iletisim_ag_gecidini_bagla(
    uygulama: FastAPI,
    yonetici: YetkiliCihazYoneticisi,
    *,
    kok_yol: str = "/cihaz-iletisimi",
) -> CihazIletisimAgGecidi:
    return CihazIletisimAgGecidi(
        yonetici,
        uygulama=uygulama,
        kok_yol=kok_yol,
    )
