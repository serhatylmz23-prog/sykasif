from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_fastapi_adaptoru import RuntimeFastApiAdaptoru
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_http_api import RuntimeHttpApi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_markdown import RuntimeMarkdownSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


def _adaptor() -> RuntimeFastApiAdaptoru:
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

    return RuntimeFastApiAdaptoru(
        RuntimeHttpApi(disa_aktarim)
    )


def test_json_rotasi_dogru_yanit_doner():
    yanit = _adaptor().rota_isle("/runtime/json")

    assert yanit.durum_kodu == 200
    assert yanit.icerik_turu == "application/json; charset=utf-8"
    assert "durum" in yanit.govde


def test_html_rotasi_dogru_yanit_doner():
    yanit = _adaptor().rota_isle("/runtime/html")

    assert yanit.durum_kodu == 200
    assert yanit.icerik_turu == "text/html; charset=utf-8"
    assert "<table>" in yanit.govde


def test_bilinmeyen_rota_404_doner():
    yanit = _adaptor().rota_isle("/bilinmeyen")

    assert yanit.durum_kodu == 404
    assert yanit.icerik_turu == "text/plain; charset=utf-8"
    assert yanit.govde == "Kaynak bulunamadı"