from __future__ import annotations

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from .runtime_csv import RuntimeCsvSaglayicisi
from .runtime_disa_aktarim import RuntimeDisaAktarim
from .runtime_html import RuntimeHtmlSaglayicisi
from .runtime_http_api import RuntimeHttpApi
from .runtime_izleme import RuntimeIzlemeSaglayicisi
from .runtime_json import RuntimeJsonSaglayicisi
from .runtime_markdown import RuntimeMarkdownSaglayicisi
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
    ) -> None:

        self._api = RuntimeHttpApi(disa_aktarim)
        self._websocket = websocket_yayinci
        self._terminal = RuntimeTerminal(runtime_durumu)

    def olustur(self) -> FastAPI:

        uygulama = FastAPI(
            title="SyKaşif Runtime API",
            version="1.1",
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

            await websocket.send_json(
                self._websocket.baglanti_mesaji()
            )

            try:

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

        return uygulama


def uygulama_olustur() -> FastAPI:

    servis = RuntimeServisi()

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

    return RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket_yayinci,
        servis.durum,
    ).olustur()


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        uygulama_olustur(),
        host="0.0.0.0",
        port=8000,
    )
