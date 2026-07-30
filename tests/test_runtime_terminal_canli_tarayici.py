from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)
from syk_simulasyon.runtime_terminal import RuntimeTerminal


def test_terminal_eski_html_sozlesmesini_korur():
    html = RuntimeTerminal().html()

    assert (
        "<dt>Aktif Adım</dt><dd>Beklemede</dd>"
        in html
    )
    assert (
        "<dt>Çalışma Durumu</dt>"
        "<dd>başlatılıyor</dd>"
        in html
    )
    assert (
        "<dt>Genel İlerleme</dt><dd>%0</dd>"
        in html
    )


def test_terminal_panel_alanlarini_basliktan_bulur():
    html = RuntimeTerminal().html()

    assert 'tanimDegeriniBul("Aktif Adım")' in html
    assert (
        'tanimDegeriniBul("Çalışma Durumu")'
        in html
    )
    assert (
        'tanimDegeriniBul("Genel İlerleme")'
        in html
    )
    assert 'kartDegeriniBul("WebSocket:")' in html


def test_terminal_mevcut_websocket_rotasina_baglanir():
    html = RuntimeTerminal().html()

    assert "new WebSocket(adres)" in html
    assert "/ws/runtime" in html
    assert 'soket.send("yenile")' in html
    assert "window.setInterval" in html
    assert "window.setTimeout" in html


def test_terminal_canli_degerleri_metin_olarak_yazar():
    html = RuntimeTerminal().html()

    assert "gorunum.aktif_modul" in html
    assert "gorunum.durum" in html
    assert "gorunum.ilerleme_yuzdesi" in html
    assert ".textContent" in html
    assert ".innerHTML" not in html


def test_terminal_baglanti_kopunca_yeniden_baglanir():
    html = RuntimeTerminal().html()

    assert '"close"' in html
    assert '"error"' in html
    assert "yenidenBaglanmayiPlanla()" in html
    assert "BAĞLANTI KESİLDİ" in html
    assert "3000" in html
    assert "2000" in html


def test_terminal_endpointi_canli_betigi_doner():
    istemci = TestClient(uygulama_olustur())

    yanit = istemci.get("/terminal")

    assert yanit.status_code == 200
    assert "new WebSocket(adres)" in yanit.text
    assert "/ws/runtime" in yanit.text
