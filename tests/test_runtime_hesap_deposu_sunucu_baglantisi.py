from pathlib import Path

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_fastapi_sunucusu import (
    RuntimeFastApiSunucusu,
)
from syk_simulasyon.runtime_hesap_deposu import (
    RuntimeHesapDeposu,
)
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_markdown import (
    RuntimeMarkdownSaglayicisi,
)
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_websocket import (
    RuntimeWebSocketYayincisi,
)
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


class TestKoruyucusu:
    ON_EK = b"TEST:"

    def koru(self, veri: bytes) -> bytes:
        return self.ON_EK + veri[::-1]

    def ac(self, veri: bytes) -> bytes:
        if not veri.startswith(self.ON_EK):
            raise ValueError("Gecersiz korumali veri.")

        return veri[len(self.ON_EK):][::-1]


def _sunucu(tmp_path: Path):
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

    websocket = RuntimeWebSocketYayincisi(
        gorunum,
        servis.durum.sistem_hazirlik_ozeti,
    )

    depo = RuntimeHesapDeposu(
        tmp_path / "guvenlik" / "hesaplar.db",
        koruyucu=TestKoruyucusu(),
    )

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket,
        servis.durum,
        runtime_servisi=servis,
        hesap_deposu=depo,
    ).olustur()

    return uygulama, depo


def test_hesap_deposu_sunucuya_baglanir(tmp_path):
    uygulama, depo = _sunucu(tmp_path)

    assert uygulama.state.runtime_hesap_deposu is depo


def test_bagli_depo_hesap_saklar(tmp_path):
    uygulama, depo = _sunucu(tmp_path)

    hesap = depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola="yalnizca-test-parolasi",
        tur_sayisi=100_000,
    )

    bulunan = (
        uygulama.state.runtime_hesap_deposu
        .kimlikle_hesap_bul("kurucu")
    )

    assert bulunan is not None
    assert bulunan.hesap_kimligi == hesap.hesap_kimligi


def test_baglanti_runtime_health_rotasini_bozmaz(tmp_path):
    uygulama, _depo = _sunucu(tmp_path)

    istemci = TestClient(
        uygulama,
        follow_redirects=False,
    )

    yanit = istemci.get("/runtime/health")

    assert yanit.status_code == 200
