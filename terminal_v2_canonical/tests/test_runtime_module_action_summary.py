from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def setup_function():
    response = client.delete(
        "/api/v2/modul-islemleri/gecmis"
    )

    assert response.status_code == 200


def test_empty_action_summary():
    response = client.get(
        "/api/v2/modul-islemleri/ozet"
    )

    assert response.status_code == 200

    veri = response.json()

    assert veri["toplam"] == 0
    assert veri["basarili"] == 0
    assert veri["hatali"] == 0
    assert veri["moduller"] == {}
    assert veri["son_kayit"] is None


def test_action_summary_counts_success_and_failure():
    client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "rapor",
            "islem": "Yeni rapor olu\u015ftur",
            "kaynak": "test",
        },
    )

    client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "harita",
            "islem": "Ge\u00e7ersiz i\u015flem",
            "kaynak": "test",
        },
    )

    veri = client.get(
        "/api/v2/modul-islemleri/ozet"
    ).json()

    assert veri["toplam"] == 2
    assert veri["basarili"] == 1
    assert veri["hatali"] == 1
    assert veri["moduller"]["rapor"] == 1
    assert veri["moduller"]["harita"] == 1
    assert veri["son_kayit"]["basarili"] is False


def test_pwa_action_summary_client_is_served():
    response = client.get(
        "/pwa/module_history.js"
    )

    assert response.status_code == 200

    text = response.text

    assert (
        "/api/v2/modul-islemleri/ozet"
        in text
    )
    assert "modulIslemOzeti" in text
    assert "window.SyKasifModuleActionSummary" in text


def test_pwa_summary_refreshes_after_actions():
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
    assert "ozetGetir()" in text
