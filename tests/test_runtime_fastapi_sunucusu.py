from fastapi.testclient import TestClient

from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_fastapi_sunucusu import RuntimeFastApiSunucusu
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_markdown import RuntimeMarkdownSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


def _istemci() -> TestClient:
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

    uygulama = RuntimeFastApiSunucusu(disa_aktarim).olustur()

    return TestClient(uygulama)


def test_json_endpointi_calisir():
    yanit = _istemci().get("/runtime/json")

    assert yanit.status_code == 200
    assert "durum" in yanit.json()


def test_html_endpointi_calisir():
    yanit = _istemci().get("/runtime/html")

    assert yanit.status_code == 200
    assert "<table>" in yanit.text


def test_xml_endpointi_calisir():
    yanit = _istemci().get("/runtime/xml")

    assert yanit.status_code == 200
    assert "<runtime>" in yanit.text


def test_bilinmeyen_rota_404_doner():
    yanit = _istemci().get("/bilinmeyen")

    assert yanit.status_code == 404