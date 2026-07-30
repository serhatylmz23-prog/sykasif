from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from .runtime_csv import RuntimeCsvSaglayicisi
from .runtime_disa_aktarim import RuntimeDisaAktarim
from .runtime_html import RuntimeHtmlSaglayicisi
from .runtime_http_api import RuntimeHttpApi
from .runtime_izleme import RuntimeIzlemeSaglayicisi
from .runtime_json import RuntimeJsonSaglayicisi
from .runtime_markdown import RuntimeMarkdownSaglayicisi
from .runtime_olay_gunlugu import (
    RuntimeOlayGunluguButunlukHatasi,
)
from .runtime_servisi import RuntimeServisi
from .runtime_secure_export import (
    ExportRole,
    ExportSecurityProfile,
    SecureExportViewProvider,
)
from .runtime_durumu import RuntimeDurumu
from .runtime_terminal import RuntimeTerminal
from .runtime_websocket import RuntimeWebSocketYayincisi
from .runtime_xml import RuntimeXmlSaglayicisi
from .runtime_yaml import RuntimeYamlSaglayicisi


class RuntimeFastApiSunucusu:

    def __init__(
        self,
        disa_aktarim: RuntimeDisaAktarim,
        websocket_yayinci: RuntimeWebSocketYayincisi | None = None,
        runtime_durumu: RuntimeDurumu | None = None,
        runtime_servisi: RuntimeServisi | None = None,
    ) -> None:

        self._api = RuntimeHttpApi(disa_aktarim)
        self._websocket = websocket_yayinci
        self._terminal = RuntimeTerminal(runtime_durumu)
        self._runtime_servisi = runtime_servisi

    def olustur(self) -> FastAPI:

        uygulama = FastAPI(
            title="SyKaşif Runtime API",
            version="1.1",
        )

        @uygulama.get("/runtime/health")
        def runtime_sagligi() -> JSONResponse:
            servis = self._runtime_servisi

            if servis is None:
                return JSONResponse(
                    status_code=200,
                    content={
                        "durum": "?al???yor",
                        "hazir": True,
                        "kalici_gunluk": {
                            "etkin": False,
                            "butunluk": "kullan?lm?yor",
                            "yol": None,
                            "kayit_sayisi": 0,
                        },
                    },
                )

            gunluk = servis.olay_gunlugu

            if gunluk is None:
                return JSONResponse(
                    status_code=200,
                    content={
                        "durum": "?al???yor",
                        "hazir": True,
                        "kalici_gunluk": {
                            "etkin": False,
                            "butunluk": "kullan?lm?yor",
                            "yol": None,
                            "kayit_sayisi": len(
                                servis.olay_gecmisi()
                            ),
                        },
                    },
                )

            try:
                olaylar = gunluk.olaylari_oku()
                gunluk.butunlugu_dogrula()
            except RuntimeOlayGunluguButunlukHatasi as hata:
                return JSONResponse(
                    status_code=503,
                    content={
                        "durum": "hatal?",
                        "hazir": False,
                        "kalici_gunluk": {
                            "etkin": True,
                            "butunluk": "bozuk",
                            "yol": str(gunluk.yol),
                            "kayit_sayisi": None,
                        },
                        "hata": str(hata),
                    },
                )

            return JSONResponse(
                status_code=200,
                content={
                    "durum": "?al???yor",
                    "hazir": True,
                    "kalici_gunluk": {
                        "etkin": True,
                        "butunluk": "sa?lam",
                        "yol": str(gunluk.yol),
                        "kayit_sayisi": len(olaylar),
                    },
                },
            )

        @uygulama.get("/terminal")
        def terminal() -> Response:

            return Response(
                content=self._terminal.html(),
                media_type="text/html; charset=utf-8",
            )

        @uygulama.get("/runtime/json")
        def runtime_json() -> Response:

            durum, govde = self._api.json()

            return Response(
                content=govde,
                status_code=durum,
                media_type="application/json",
            )

        @uygulama.get("/runtime/html")
        def runtime_html() -> Response:

            durum, govde = self._api.html()

            return Response(
                content=govde,
                status_code=durum,
                media_type="text/html",
            )

        @uygulama.get("/runtime/csv")
        def runtime_csv() -> Response:

            durum, govde = self._api.csv()

            return Response(
                content=govde,
                status_code=durum,
                media_type="text/csv",
            )

        @uygulama.get("/runtime/markdown")
        def runtime_markdown() -> Response:

            durum, govde = self._api.markdown()

            return Response(
                content=govde,
                status_code=durum,
                media_type="text/markdown",
            )

        @uygulama.get("/runtime/xml")
        def runtime_xml() -> Response:

            durum, govde = self._api.xml()

            return Response(
                content=govde,
                status_code=durum,
                media_type="application/xml",
            )

        @uygulama.get("/runtime/yaml")
        def runtime_yaml() -> Response:

            durum, govde = self._api.yaml()

            return Response(
                content=govde,
                status_code=durum,
                media_type="application/yaml",
            )

        @uygulama.websocket("/ws/runtime")
        async def runtime_websocket(
            websocket: WebSocket,
        ) -> None:

            await websocket.accept()

            if self._websocket is None:
                await websocket.send_json(
                    {
                        "durum": "kullanılamıyor",
                        "mesaj": (
                            "WebSocket yayıncısı yapılandırılmadı."
                        ),
                    }
                )
                await websocket.close(code=1011)
                return

            olay_kuyrugu: asyncio.Queue[None] = asyncio.Queue()
            olay_dongusu = asyncio.get_running_loop()

            def runtime_olayi_geldi(_olay: object) -> None:
                olay_dongusu.call_soon_threadsafe(
                    olay_kuyrugu.put_nowait,
                    None,
                )

            bildirim_merkezi = (
                self._runtime_servisi.bildirim_merkezi
                if self._runtime_servisi is not None
                else None
            )

            if bildirim_merkezi is not None:
                bildirim_merkezi.abone_ekle(
                    runtime_olayi_geldi
                )

            olay_yayin_gorevi: asyncio.Task[None] | None = None

            async def olaylari_yayinla() -> None:
                while True:
                    await olay_kuyrugu.get()

                    try:
                        await websocket.send_json(
                            self._websocket.guncelleme_mesaji()
                        )
                    except (
                        WebSocketDisconnect,
                        RuntimeError,
                    ):
                        return

            try:
                await websocket.send_json(
                    self._websocket.baglanti_mesaji()
                )

                if bildirim_merkezi is not None:
                    olay_yayin_gorevi = asyncio.create_task(
                        olaylari_yayinla()
                    )

                while True:
                    komut = await websocket.receive_text()

                    if komut.lower() in {
                        "güncelle",
                        "guncelle",
                        "yenile",
                    }:
                        await websocket.send_json(
                            self._websocket.guncelleme_mesaji()
                        )
                    else:
                        await websocket.send_json(
                            self._websocket.bilinmeyen_komut(
                                komut
                            )
                        )

            except WebSocketDisconnect:
                pass
            finally:
                if bildirim_merkezi is not None:
                    bildirim_merkezi.abone_sil(
                        runtime_olayi_geldi
                    )

                if olay_yayin_gorevi is not None:
                    if not olay_yayin_gorevi.done():
                        olay_yayin_gorevi.cancel()

                    await asyncio.gather(
                        olay_yayin_gorevi,
                        return_exceptions=True,
                    )

        return uygulama


def uygulama_olustur() -> FastAPI:

    olay_gunlugu_yolu = os.getenv(
        "SYK_RUNTIME_OLAY_GUNLUGU"
    )

    servis = RuntimeServisi(
        olay_gunlugu_yolu or None
    )

    gorunum = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    guvenli_gorunum = SecureExportViewProvider(
        gorunum,
        ExportSecurityProfile.from_environment(
            role=ExportRole.PUBLIC,
        ),
    )

    disa_aktarim = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(guvenli_gorunum),
        RuntimeCsvSaglayicisi(guvenli_gorunum),
        RuntimeHtmlSaglayicisi(guvenli_gorunum),
        RuntimeMarkdownSaglayicisi(guvenli_gorunum),
        RuntimeXmlSaglayicisi(guvenli_gorunum),
        RuntimeYamlSaglayicisi(guvenli_gorunum),
    )

    websocket_yayinci = RuntimeWebSocketYayincisi(
        gorunum,
        servis.durum.sistem_hazirlik_ozeti,
    )

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket_yayinci,
        servis.durum,
        runtime_servisi=servis,
    ).olustur()

    uygulama.state.runtime_servisi = servis
    uygulama.state.runtime_olay_gunlugu_yolu = (
        olay_gunlugu_yolu
    )

    return uygulama


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        uygulama_olustur(),
        host="0.0.0.0",
        port=8000,
    )
