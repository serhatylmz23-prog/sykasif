from fastapi.testclient import TestClient

from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_durumu import RuntimeDurumTuru
from syk_simulasyon.runtime_fastapi_sunucusu import (
    RuntimeFastApiSunucusu,
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


def _istemci_ve_servis() -> tuple[TestClient, RuntimeServisi]:
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

    return TestClient(uygulama), servis


def test_runtime_olayi_websockete_komutsuz_itilir():
    istemci, servis = _istemci_ve_servis()

    with istemci.websocket_connect("/ws/runtime") as websocket:
        baglanti = websocket.receive_json()

        assert baglanti["mesaj"] == (
            "SyOtağı bağlantısı kuruldu"
        )

        servis.durum.adimlari_guncelle(
            tamamlanan_adim=3,
            toplam_adim=4,
            aktif_modul="Olay Tetiklemeli Canlı Yayın",
        )
        servis.durum.durum_guncelle(
            durum=RuntimeDurumTuru.CALISIYOR,
        )

        servis.olay_uret(
            arastirma_kimligi="SPR002",
            deney_numarasi="DSP0012",
        )

        guncelleme = websocket.receive_json()

        assert guncelleme["mesaj"] == (
            "Canlı görünüm güncellendi"
        )
        assert guncelleme["gorunum"]["aktif_modul"] == (
            "Olay Tetiklemeli Canlı Yayın"
        )
        assert guncelleme["gorunum"]["ilerleme_yuzdesi"] == 75.0
        assert guncelleme["gorunum"]["olay_sayisi"] == 1


def test_websocket_kapaninca_runtime_aboneligi_kaldirilir():
    istemci, servis = _istemci_ve_servis()

    assert servis.bildirim_merkezi.abone_sayisi == 0

    with istemci.websocket_connect("/ws/runtime") as websocket:
        websocket.receive_json()

        assert servis.bildirim_merkezi.abone_sayisi == 1

    assert servis.bildirim_merkezi.abone_sayisi == 0
