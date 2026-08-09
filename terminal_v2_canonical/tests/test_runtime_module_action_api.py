from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_valid_module_action_is_accepted():
    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "rapor",
            "islem": "Yeni rapor olu\u015ftur",
            "kaynak": "pwa",
        },
    )

    assert response.status_code == 200

    veri = response.json()

    assert veri["basarili"] is True
    assert veri["modul_kodu"] == "rapor"
    assert veri["kaynak"] == "pwa"
    assert (
        veri["mesaj"]
        == "\u0130\u015flem se\u00e7ildi: Yeni rapor olu\u015ftur"
    )


def test_unknown_module_action_is_rejected():
    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "harita",
            "islem": "Bilinmeyen i\u015flem",
        },
    )

    veri = response.json()

    assert veri["basarili"] is False
    assert (
        veri["mesaj"]
        == "\u0130\u015flem mod\u00fcl katalo\u011funda bulunamad\u0131."
    )


def test_empty_module_action_is_rejected():
    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "analiz",
            "islem": "   ",
        },
    )

    veri = response.json()

    assert veri["basarili"] is False
    assert (
        veri["mesaj"]
        == "\u0130\u015flem se\u00e7imi bo\u015f olamaz."
    )


def test_unknown_module_uses_dashboard_fallback():
    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "bilinmeyen",
            "islem": (
                "Runtime ba\u011flant\u0131 durumunu izle"
            ),
        },
    )

    veri = response.json()

    assert veri["basarili"] is True
    assert veri["modul_kodu"] == "dashboard"
