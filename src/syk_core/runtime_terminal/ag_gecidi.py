"""SyKaşif terminal ağ geçidi ve Türkçe HTTP arayüzü."""

from __future__ import annotations

import json
from collections import deque
from datetime import UTC, datetime
from ipaddress import ip_address
from typing import Any, Callable
from uuid import uuid4

from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Request,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from syk_core.runtime_kernel import (
    RuntimeEvent,
    RuntimeEventBus,
)

from .ag_modelleri import (
    AgGecidiAyarlari,
    AgGecidiHatasi,
    AgIstegi,
    IstekDurumu,
    IstekTuru,
)
from .modeller import (
    BildirimTuru,
    CihazTuru,
    KomutTuru,
    TerminalHatasi,
    YetkiliCihazTanimi,
    YetkiSeviyesi,
)
from .oturum_modelleri import (
    OturumHatasi,
)
from .oturum_yoneticisi import (
    TerminalOturumYoneticisi,
)
from .terminal import CalismaTerminali


class CihazKayitGirdisi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    cihaz_kimligi: str = Field(
        alias="cihaz_kimliği",
        min_length=1,
        max_length=200,
    )
    ad: str = Field(
        min_length=1,
        max_length=200,
    )
    cihaz_turu: CihazTuru = Field(
        alias="cihaz_türü"
    )
    yetki_seviyesi: YetkiSeviyesi = Field(
        alias="yetki_seviyesi"
    )
    cihaz_parmak_izi: str = Field(
        alias="cihaz_parmak_izi",
        min_length=1,
        max_length=500,
    )
    aciklama: str | None = Field(
        default=None,
        alias="açıklama",
        max_length=1000,
    )
    veri: dict[str, Any] = Field(
        default_factory=dict
    )


class OturumAcmaGirdisi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    cihaz_kimligi: str = Field(
        alias="cihaz_kimliği",
        min_length=1,
        max_length=200,
    )
    cihaz_parmak_izi: str = Field(
        alias="cihaz_parmak_izi",
        min_length=1,
        max_length=500,
    )
    veri: dict[str, Any] = Field(
        default_factory=dict
    )


class CanlilikGirdisi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    oturum_kimligi: str = Field(
        alias="oturum_kimliği",
        min_length=1,
        max_length=300,
    )


class KomutGirdisi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    oturum_kimligi: str = Field(
        alias="oturum_kimliği",
        min_length=1,
        max_length=300,
    )
    hedef_cihaz_kimligi: str = Field(
        alias="hedef_cihaz_kimliği",
        min_length=1,
        max_length=200,
    )
    komut_turu: KomutTuru = Field(
        alias="komut_türü"
    )
    icerik: dict[str, Any] = Field(
        default_factory=dict,
        alias="içerik",
    )
    gerekce: str | None = Field(
        default=None,
        alias="gerekçe",
        max_length=2000,
    )
    onaylayan: str | None = Field(
        default=None,
        max_length=300,
    )
    hemen_calistir: bool = Field(
        default=True,
        alias="hemen_çalıştır",
    )


class BildirimGirdisi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    oturum_kimligi: str = Field(
        alias="oturum_kimliği",
        min_length=1,
        max_length=300,
    )
    bildirim_turu: BildirimTuru = Field(
        alias="bildirim_türü"
    )
    baslik: str = Field(
        alias="başlık",
        min_length=1,
        max_length=300,
    )
    aciklama: str = Field(
        alias="açıklama",
        min_length=1,
        max_length=4000,
    )
    hedef_cihaz_kimligi: str | None = Field(
        default=None,
        alias="hedef_cihaz_kimliği",
        max_length=200,
    )
    veri: dict[str, Any] = Field(
        default_factory=dict
    )


class OturumKapatmaGirdisi(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    oturum_kimligi: str = Field(
        alias="oturum_kimliği",
        min_length=1,
        max_length=300,
    )
    gerekce: str = Field(
        alias="gerekçe",
        min_length=1,
        max_length=2000,
    )


class TerminalAgGecidi:
    """Terminal çekirdeğini Türkçe ağ uçlarına bağlar."""

    def __init__(
        self,
        terminal: CalismaTerminali,
        oturum_yoneticisi: TerminalOturumYoneticisi,
        *,
        ayarlar: AgGecidiAyarlari | None = None,
        olay_hatti: RuntimeEventBus | None = None,
        saat: Callable[[], datetime] | None = None,
    ) -> None:
        self.terminal = terminal
        self.oturum_yoneticisi = (
            oturum_yoneticisi
        )
        self.ayarlar = (
            ayarlar
            or AgGecidiAyarlari()
        )
        self.olay_hatti = (
            olay_hatti
            or terminal.olay_hatti
        )
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self._istekler: dict[
            str,
            AgIstegi,
        ] = {}

        self._istek_sirasi: deque[
            str
        ] = deque(
            maxlen=self.ayarlar.istek_gecmisi_siniri
        )

        self.uygulama = FastAPI(
            title="SyKaşif Terminal Ağ Geçidi",
            description=(
                "Yetkili cihazlar için Türkçe "
                "ve insan onaylı terminal arayüzü."
            ),
            version="0.6.4",
            docs_url="/belgeler",
            redoc_url=None,
            openapi_url="/aciklama.json",
        )

        self._hata_yakalayicilarini_kaydet()
        self._yollari_kaydet()

    def istekleri_listele(
        self,
    ) -> tuple[AgIstegi, ...]:
        return tuple(
            self._istekler[kimlik]
            for kimlik in self._istek_sirasi
            if kimlik in self._istekler
        )

    def istek_getir(
        self,
        istek_kimligi: str,
    ) -> AgIstegi:
        try:
            return self._istekler[
                istek_kimligi
            ]
        except KeyError as hata:
            raise AgGecidiHatasi(
                "İstek bulunamadı: "
                f"{istek_kimligi}"
            ) from hata

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        istekler = self.istekleri_listele()

        return {
            "ağ_geçidi": "hazır",
            "ayarlar": self.ayarlar.sozluk(),
            "toplam_istek_sayısı": len(
                istekler
            ),
            "işlenen_istek_sayısı": sum(
                1
                for istek in istekler
                if istek.durum
                is IstekDurumu.ISLENDI
            ),
            "reddedilen_istek_sayısı": sum(
                1
                for istek in istekler
                if istek.durum
                is IstekDurumu.REDDEDILDI
            ),
            "hatalı_istek_sayısı": sum(
                1
                for istek in istekler
                if istek.durum
                is IstekDurumu.HATA
            ),
            "terminal": self.terminal.durum_ozeti(),
            "oturumlar": (
                self.oturum_yoneticisi.durum_ozeti()
            ),
        }

    def _hata_yakalayicilarini_kaydet(
        self,
    ) -> None:
        @self.uygulama.exception_handler(
            TerminalHatasi
        )
        async def terminal_hatasi_yakala(
            request: Request,
            hata: TerminalHatasi,
        ) -> JSONResponse:
            return JSONResponse(
                status_code=400,
                content={
                    "başarılı": False,
                    "hata": str(hata),
                    "hata_türü": "terminal_hatası",
                },
            )

        @self.uygulama.exception_handler(
            OturumHatasi
        )
        async def oturum_hatasi_yakala(
            request: Request,
            hata: OturumHatasi,
        ) -> JSONResponse:
            return JSONResponse(
                status_code=401,
                content={
                    "başarılı": False,
                    "hata": str(hata),
                    "hata_türü": "oturum_hatası",
                },
            )

        @self.uygulama.exception_handler(
            AgGecidiHatasi
        )
        async def ag_hatasi_yakala(
            request: Request,
            hata: AgGecidiHatasi,
        ) -> JSONResponse:
            return JSONResponse(
                status_code=400,
                content={
                    "başarılı": False,
                    "hata": str(hata),
                    "hata_türü": "ağ_geçidi_hatası",
                },
            )

    def _yollari_kaydet(
        self,
    ) -> None:
        @self.uygulama.get(
            "/",
            tags=["Sistem"],
        )
        async def ana_sayfa() -> dict[str, Any]:
            return {
                "başarılı": True,
                "sistem": "SyKaşif",
                "hizmet": "Terminal Ağ Geçidi",
                "durum": "hazır",
                "dil": "Türkçe",
            }

        @self.uygulama.get(
            "/saglik",
            tags=["Sistem"],
        )
        async def saglik() -> dict[str, Any]:
            return {
                "başarılı": True,
                "durum": "sağlıklı",
                "zaman": self._saat().isoformat(),
            }

        @self.uygulama.get(
            "/durum",
            tags=["Sistem"],
        )
        async def durum(
            x_oturum_kimligi: str | None = Header(
                default=None,
                alias="X-Oturum-Kimligi",
            ),
        ) -> dict[str, Any]:
            if x_oturum_kimligi is not None:
                self._oturumu_dogrula(
                    x_oturum_kimligi
                )

            return {
                "başarılı": True,
                "durum": self.durum_ozeti(),
            }

        @self.uygulama.post(
            "/cihazlar/kaydet",
            tags=["Cihazlar"],
            status_code=201,
        )
        async def cihaz_kaydet(
            girdi: CihazKayitGirdisi,
            request: Request,
        ) -> dict[str, Any]:
            istek = self._istek_olustur(
                istek_turu=IstekTuru.CIHAZ_KAYDI,
                request=request,
                cihaz_kimligi=(
                    girdi.cihaz_kimligi
                ),
                icerik=girdi.model_dump(
                    by_alias=True
                ),
            )

            try:
                self._yerel_ag_kontrolu(
                    request
                )

                cihaz = self.terminal.cihaz_kaydet(
                    YetkiliCihazTanimi(
                        cihaz_kimligi=(
                            girdi.cihaz_kimligi
                        ),
                        ad=girdi.ad,
                        cihaz_turu=(
                            girdi.cihaz_turu
                        ),
                        yetki_seviyesi=(
                            girdi.yetki_seviyesi
                        ),
                        cihaz_parmak_izi=(
                            girdi.cihaz_parmak_izi
                        ),
                        aciklama=(
                            girdi.aciklama
                        ),
                        veri=dict(girdi.veri),
                    )
                )

                return self._istegi_tamamla(
                    istek,
                    {
                        "başarılı": True,
                        "cihaz": cihaz.sozluk(),
                    },
                )

            except Exception as hata:
                self._istegi_hata_yap(
                    istek,
                    hata,
                )
                raise

        @self.uygulama.get(
            "/cihazlar",
            tags=["Cihazlar"],
        )
        async def cihazlari_listele(
            x_oturum_kimligi: str = Header(
                alias="X-Oturum-Kimligi"
            ),
        ) -> dict[str, Any]:
            self._oturumu_dogrula(
                x_oturum_kimligi
            )

            return {
                "başarılı": True,
                "cihazlar": [
                    cihaz.sozluk()
                    for cihaz
                    in self.terminal.cihazlari_listele()
                ],
            }

        @self.uygulama.post(
            "/oturumlar/ac",
            tags=["Oturumlar"],
            status_code=201,
        )
        async def oturum_ac(
            girdi: OturumAcmaGirdisi,
            request: Request,
        ) -> dict[str, Any]:
            istek = self._istek_olustur(
                istek_turu=IstekTuru.OTURUM_ACMA,
                request=request,
                cihaz_kimligi=(
                    girdi.cihaz_kimligi
                ),
                icerik={
                    "cihaz_kimliği": (
                        girdi.cihaz_kimligi
                    ),
                    "veri": dict(girdi.veri),
                },
            )

            try:
                self._yerel_ag_kontrolu(
                    request
                )

                oturum = (
                    self.oturum_yoneticisi.oturum_ac(
                        cihaz_kimligi=(
                            girdi.cihaz_kimligi
                        ),
                        cihaz_parmak_izi=(
                            girdi.cihaz_parmak_izi
                        ),
                        veri=dict(girdi.veri),
                    )
                )

                yanit = {
                    "başarılı": True,
                    "oturum": oturum.sozluk(),
                }

                if (
                    self.ayarlar
                    .oturum_anahtarini_yanitta_goster
                ):
                    yanit[
                        "oturum_anahtarı"
                    ] = oturum.oturum_anahtari

                return self._istegi_tamamla(
                    istek,
                    yanit,
                )

            except Exception as hata:
                self._istegi_hata_yap(
                    istek,
                    hata,
                )
                raise

        @self.uygulama.post(
            "/oturumlar/canlilik",
            tags=["Oturumlar"],
        )
        async def canlilik(
            girdi: CanlilikGirdisi,
            request: Request,
        ) -> dict[str, Any]:
            istek = self._istek_olustur(
                istek_turu=IstekTuru.CANLILIK,
                request=request,
                oturum_kimligi=(
                    girdi.oturum_kimligi
                ),
                icerik=girdi.model_dump(
                    by_alias=True
                ),
            )

            try:
                oturum = (
                    self.oturum_yoneticisi.canlilik_bildir(
                        girdi.oturum_kimligi
                    )
                )

                return self._istegi_tamamla(
                    istek,
                    {
                        "başarılı": True,
                        "oturum": oturum.sozluk(),
                    },
                )

            except Exception as hata:
                self._istegi_hata_yap(
                    istek,
                    hata,
                )
                raise

        @self.uygulama.post(
            "/oturumlar/kapat",
            tags=["Oturumlar"],
        )
        async def oturum_kapat(
            girdi: OturumKapatmaGirdisi,
            request: Request,
        ) -> dict[str, Any]:
            istek = self._istek_olustur(
                istek_turu=IstekTuru.OTURUM_KAPATMA,
                request=request,
                oturum_kimligi=(
                    girdi.oturum_kimligi
                ),
                icerik=girdi.model_dump(
                    by_alias=True
                ),
            )

            try:
                oturum = (
                    self.oturum_yoneticisi
                    .oturumu_sonlandir(
                        girdi.oturum_kimligi,
                        gerekce=girdi.gerekce,
                    )
                )

                return self._istegi_tamamla(
                    istek,
                    {
                        "başarılı": True,
                        "oturum": oturum.sozluk(),
                    },
                )

            except Exception as hata:
                self._istegi_hata_yap(
                    istek,
                    hata,
                )
                raise

        @self.uygulama.post(
            "/komutlar",
            tags=["Komutlar"],
            status_code=201,
        )
        async def komut_olustur(
            girdi: KomutGirdisi,
            request: Request,
        ) -> dict[str, Any]:
            oturum = self._oturumu_dogrula(
                girdi.oturum_kimligi
            )

            istek = self._istek_olustur(
                istek_turu=IstekTuru.KOMUT,
                request=request,
                cihaz_kimligi=(
                    oturum.cihaz_kimligi
                ),
                oturum_kimligi=(
                    girdi.oturum_kimligi
                ),
                icerik=girdi.model_dump(
                    by_alias=True
                ),
            )

            try:
                komut = self.terminal.komut_olustur(
                    kaynak_cihaz_kimligi=(
                        oturum.cihaz_kimligi
                    ),
                    hedef_cihaz_kimligi=(
                        girdi.hedef_cihaz_kimligi
                    ),
                    komut_turu=(
                        girdi.komut_turu
                    ),
                    icerik=dict(girdi.icerik),
                    gerekce=girdi.gerekce,
                    onaylayan=(
                        girdi.onaylayan
                    ),
                )

                if girdi.hemen_calistir:
                    self.terminal.siradaki_komutu_calistir()

                return self._istegi_tamamla(
                    istek,
                    {
                        "başarılı": True,
                        "komut": komut.sozluk(),
                    },
                )

            except Exception as hata:
                self._istegi_hata_yap(
                    istek,
                    hata,
                )
                raise

        @self.uygulama.get(
            "/komutlar",
            tags=["Komutlar"],
        )
        async def komutlari_listele(
            x_oturum_kimligi: str = Header(
                alias="X-Oturum-Kimligi"
            ),
        ) -> dict[str, Any]:
            self._oturumu_dogrula(
                x_oturum_kimligi
            )

            return {
                "başarılı": True,
                "komutlar": [
                    komut.sozluk()
                    for komut
                    in self.terminal.komutlari_listele()
                ],
            }

        @self.uygulama.post(
            "/bildirimler",
            tags=["Bildirimler"],
            status_code=201,
        )
        async def bildirim_olustur(
            girdi: BildirimGirdisi,
            request: Request,
        ) -> dict[str, Any]:
            oturum = self._oturumu_dogrula(
                girdi.oturum_kimligi
            )

            istek = self._istek_olustur(
                istek_turu=IstekTuru.BILDIRIM,
                request=request,
                cihaz_kimligi=(
                    oturum.cihaz_kimligi
                ),
                oturum_kimligi=(
                    girdi.oturum_kimligi
                ),
                icerik=girdi.model_dump(
                    by_alias=True
                ),
            )

            try:
                bildirim = (
                    self.terminal.bildirim_olustur(
                        bildirim_turu=(
                            girdi.bildirim_turu
                        ),
                        baslik=girdi.baslik,
                        aciklama=girdi.aciklama,
                        hedef_cihaz_kimligi=(
                            girdi.hedef_cihaz_kimligi
                        ),
                        veri=dict(girdi.veri),
                    )
                )

                return self._istegi_tamamla(
                    istek,
                    {
                        "başarılı": True,
                        "bildirim": (
                            bildirim.sozluk()
                        ),
                    },
                )

            except Exception as hata:
                self._istegi_hata_yap(
                    istek,
                    hata,
                )
                raise

        @self.uygulama.get(
            "/bildirimler",
            tags=["Bildirimler"],
        )
        async def bildirimleri_listele(
            x_oturum_kimligi: str = Header(
                alias="X-Oturum-Kimligi"
            ),
        ) -> dict[str, Any]:
            self._oturumu_dogrula(
                x_oturum_kimligi
            )

            return {
                "başarılı": True,
                "bildirimler": [
                    bildirim.sozluk()
                    for bildirim
                    in self.terminal.bildirimler
                ],
            }

        @self.uygulama.get(
            "/istekler",
            tags=["Denetim"],
        )
        async def istekleri_listele(
            x_oturum_kimligi: str = Header(
                alias="X-Oturum-Kimligi"
            ),
        ) -> dict[str, Any]:
            self._oturumu_dogrula(
                x_oturum_kimligi
            )

            return {
                "başarılı": True,
                "istekler": [
                    istek.sozluk()
                    for istek
                    in self.istekleri_listele()
                ],
            }

    def _oturumu_dogrula(
        self,
        oturum_kimligi: str,
    ):
        oturum = (
            self.oturum_yoneticisi.oturum_getir(
                oturum_kimligi
            )
        )

        if not oturum.bagli_mi:
            raise OturumHatasi(
                "Oturum bağlı değil."
            )

        return oturum

    def _yerel_ag_kontrolu(
        self,
        request: Request,
    ) -> None:
        if (
            self.ayarlar
            .dis_ag_erisimine_izin_ver
        ):
            return

        istemci = request.client

        if istemci is None:
            return

        adres = istemci.host

        if adres in {
            "testclient",
            "localhost",
        }:
            return

        try:
            cozumlenen = ip_address(
                adres
            )
        except ValueError as hata:
            raise AgGecidiHatasi(
                "İstemci adresi doğrulanamadı."
            ) from hata

        if not (
            cozumlenen.is_private
            or cozumlenen.is_loopback
            or cozumlenen.is_link_local
        ):
            raise AgGecidiHatasi(
                "Dış ağdan cihaz kaydı kapalıdır."
            )

    def _istek_olustur(
        self,
        *,
        istek_turu: IstekTuru,
        request: Request,
        cihaz_kimligi: str | None = None,
        oturum_kimligi: str | None = None,
        icerik: dict[str, Any] | None = None,
    ) -> AgIstegi:
        ham_icerik = dict(
            icerik or {}
        )

        boyut = len(
            json.dumps(
                ham_icerik,
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")
        )

        if (
            boyut
            > self.ayarlar.en_fazla_icerik_bayti
        ):
            raise AgGecidiHatasi(
                "İstek içeriği izin verilen boyutu aşıyor."
            )

        istek = AgIstegi(
            istek_kimligi=(
                "SYK-AG-ISTEK-"
                + uuid4().hex.upper()
            ),
            istek_turu=istek_turu,
            olusturulma_zamani=self._saat(),
            kaynak_adres=(
                request.client.host
                if request.client
                else None
            ),
            cihaz_kimligi=cihaz_kimligi,
            oturum_kimligi=oturum_kimligi,
            durum=IstekDurumu.DOGRULANDI,
            icerik=ham_icerik,
        )

        self._istekler[
            istek.istek_kimligi
        ] = istek

        self._istek_sirasi.append(
            istek.istek_kimligi
        )

        self._olay_yayinla(
            konu="terminal.ag.istek_alindi",
            icerik={
                "istek_kimliği": (
                    istek.istek_kimligi
                ),
                "istek_türü": (
                    istek.istek_turu.value
                ),
                "cihaz_kimliği": (
                    cihaz_kimligi
                ),
            },
        )

        return istek

    def _istegi_tamamla(
        self,
        istek: AgIstegi,
        sonuc: dict[str, Any],
    ) -> dict[str, Any]:
        istek.durum = IstekDurumu.ISLENDI
        istek.sonuc = dict(sonuc)
        istek.tamamlanma_zamani = (
            self._saat()
        )

        self._olay_yayinla(
            konu="terminal.ag.istek_islendi",
            icerik={
                "istek_kimliği": (
                    istek.istek_kimligi
                ),
                "istek_türü": (
                    istek.istek_turu.value
                ),
            },
        )

        return sonuc

    def _istegi_hata_yap(
        self,
        istek: AgIstegi,
        hata: Exception,
    ) -> None:
        if isinstance(
            hata,
            (
                TerminalHatasi,
                OturumHatasi,
                AgGecidiHatasi,
            ),
        ):
            istek.durum = (
                IstekDurumu.REDDEDILDI
            )
        else:
            istek.durum = IstekDurumu.HATA

        istek.hata = str(hata)
        istek.tamamlanma_zamani = (
            self._saat()
        )

        self._olay_yayinla(
            konu="terminal.ag.istek_hata",
            icerik={
                "istek_kimliği": (
                    istek.istek_kimligi
                ),
                "hata": str(hata),
            },
        )

    def _olay_yayinla(
        self,
        *,
        konu: str,
        icerik: dict[str, Any],
    ) -> None:
        self.olay_hatti.publish(
            RuntimeEvent(
                topic=konu,
                source="terminal_ag_gecidi",
                payload=icerik,
            )
        )


def terminal_ag_uygulamasi_olustur(
    terminal: CalismaTerminali,
    oturum_yoneticisi: TerminalOturumYoneticisi,
    *,
    ayarlar: AgGecidiAyarlari | None = None,
) -> FastAPI:
    gecit = TerminalAgGecidi(
        terminal,
        oturum_yoneticisi,
        ayarlar=ayarlar,
    )

    gecit.uygulama.state.terminal_ag_gecidi = gecit

    return gecit.uygulama
