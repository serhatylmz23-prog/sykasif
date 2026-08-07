from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_module_history_client_is_served():
    response = client.get(
        "/pwa/module_history.js"
    )

    assert response.status_code == 200
    assert (
        "/api/v2/modul-islemleri/gecmis"
        in response.text
    )
    assert (
        "window.SyKasifModuleHistory"
        in response.text
    )


def test_pwa_loads_module_history_client():
    response = client.get(
        "/pwa/"
    )

    assert response.status_code == 200
    assert (
        "./module_history.js"
        in response.text
    )


def test_history_client_supports_get_and_delete():
    text = client.get(
        "/pwa/module_history.js"
    ).text

    assert '"GET"' in text
    assert '"DELETE"' in text
    assert "gecmisiGetir" in text
    assert "gecmisiTemizle" in text


def test_history_client_renders_records():
    text = client.get(
        "/pwa/module_history.js"
    ).text

    assert "modulIslemGecmisi" in text
    assert "modulIslemGecmisiListe" in text
    assert "kayitlar" in text
    assert "kayit.basarili" in text
    assert "kayit.mesaj" in text


def test_history_refreshes_after_module_action():
    text = client.get(
        "/pwa/module_history.js"
    ).text

    assert (
        "sykasif:modul-islemi-tamamlandi"
        in text
    )
    assert (
        "sykasif:modul-islemi-hata"
        in text
    )
    assert "yenile()" in text
