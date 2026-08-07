from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_pwa_module_action_client_is_served():
    response = client.get(
        "/pwa/module_actions.js"
    )

    assert response.status_code == 200
    assert (
        "/api/v2/modul-islemleri/sec"
        in response.text
    )
    assert (
        "window.SyKasifModuleActions"
        in response.text
    )


def test_pwa_loads_module_action_client():
    response = client.get("/pwa/")

    assert response.status_code == 200
    assert (
        "./module_actions.js"
        in response.text
    )


def test_action_client_posts_selected_action():
    response = client.get(
        "/pwa/module_actions.js"
    )

    text = response.text

    assert '"POST"' in text
    assert "JSON.stringify" in text
    assert "modul_kodu" in text
    assert 'kaynak: "pwa"' in text


def test_action_client_updates_live_status():
    response = client.get(
        "/pwa/module_actions.js"
    )

    text = response.text

    assert "?al???yor:" in text
    assert "sonuc.mesaj" in text
    assert 'alan.dataset.durum' in text
    assert '"basarili"' in text
    assert '"hata"' in text


def test_action_client_dispatches_result_events():
    response = client.get(
        "/pwa/module_actions.js"
    )

    text = response.text

    assert (
        "sykasif:modul-islemi-tamamlandi"
        in text
    )
    assert (
        "sykasif:modul-islemi-hata"
        in text
    )
    assert "CustomEvent(" in text


def test_action_buttons_are_rebound_after_render():
    response = client.get(
        "/pwa/module_actions.js"
    )

    text = response.text

    assert "MutationObserver" in text
    assert ".modul-islem-butonu" in text
    assert (
        "sykasif:modul-detayi-hazir"
        in text
    )
