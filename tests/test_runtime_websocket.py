from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import uygulama_olustur


def test_websocket_baglanti_mesaji():
    istemci = TestClient(uygulama_olustur())

    with istemci.websocket_connect("/ws/runtime") as websocket:
        veri = websocket.receive_json()

    assert veri["mesaj"] == "SyOtağı bağlantısı kuruldu"
    assert veri["terminal"] == "SYK-FIELD-01"


def test_websocket_guncelleme_mesaji():
    istemci = TestClient(uygulama_olustur())

    with istemci.websocket_connect("/ws/runtime") as websocket:
        websocket.receive_json()

        websocket.send_text("güncelle")

        veri = websocket.receive_json()

    assert veri["mesaj"] == "Canlı görünüm güncellendi"


def test_websocket_bilinmeyen_komut():
    istemci = TestClient(uygulama_olustur())

    with istemci.websocket_connect("/ws/runtime") as websocket:
        websocket.receive_json()

        websocket.send_text("test")

        veri = websocket.receive_json()

    assert veri["mesaj"] == "Bilinmeyen komut"
    assert veri["komut"] == "test"


def test_terminal_turkce_kontrol():
    istemci = TestClient(uygulama_olustur())

    yanit = istemci.get("/terminal")

    assert yanit.status_code == 200
    assert "SyOtağı" in yanit.text