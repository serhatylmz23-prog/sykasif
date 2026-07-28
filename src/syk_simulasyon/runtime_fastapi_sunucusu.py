from __future__ import annotations

from fastapi import FastAPI, Response

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from .runtime_csv import RuntimeCsvSaglayicisi
from .runtime_disa_aktarim import RuntimeDisaAktarim
from .runtime_html import RuntimeHtmlSaglayicisi
from .runtime_http_api import RuntimeHttpApi
from .runtime_izleme import RuntimeIzlemeSaglayicisi
from .runtime_json import RuntimeJsonSaglayicisi
from .runtime_markdown import RuntimeMarkdownSaglayicisi
from .runtime_servisi import RuntimeServisi
from .runtime_xml import RuntimeXmlSaglayicisi
from .runtime_yaml import RuntimeYamlSaglayicisi


class RuntimeFastApiSunucusu:
    """Runtime için FastAPI uygulaması oluşturur."""

    def __init__(self, disa_aktarim: RuntimeDisaAktarim) -> None:
        self._api = RuntimeHttpApi(disa_aktarim)

    def olustur(self) -> FastAPI:
        uygulama = FastAPI(
            title="SyKaşif Runtime API",
            version="1.0",
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

        return uygulama


def uygulama_olustur() -> FastAPI:
    servis = RuntimeServisi()

    gorunum = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    disa_aktarim = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(gorunum),
        RuntimeCsvSaglayicisi(gorunum),
        RuntimeHtmlSaglayicisi(gorunum),
        RuntimeMarkdownSaglayicisi(gorunum),
        RuntimeXmlSaglayicisi(gorunum),
        RuntimeYamlSaglayicisi(gorunum),
    )

    return RuntimeFastApiSunucusu(disa_aktarim).olustur()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        uygulama_olustur(),
        host="0.0.0.0",
        port=8000,
    )