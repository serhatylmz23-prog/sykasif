from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def setup_function():
    response = client.delete(
        "/api/v2/modul-islemleri/gecmis"
    )

    assert response.status_code == 200


def test_successful_action_is_saved():
    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "rapor",
            "islem": "Yeni rapor olu\u015ftur",
            "kaynak": "test",
        },
    )

    assert response.status_code == 200

    sonuc = response.json()

    assert sonuc["basarili"] is True
    assert sonuc["gecmis_boyutu"] == 1
    assert sonuc["zaman"]
    assert sonuc["sira"] == 1


def test_failed_action_is_saved():
    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "harita",
            "islem": "Ge\u00e7ersiz i\u015flem",
            "kaynak": "test",
        },
    )

    sonuc = response.json()

    assert sonuc["basarili"] is False
    assert sonuc["gecmis_boyutu"] == 1


def test_action_history_returns_latest_first():
    modul_islemleri = (
        (
            "rapor",
            "Yeni rapor olu\u015ftur",
        ),
        (
            "harita",
            "Katmanlar\u0131 g\u00f6r\u00fcnt\u00fcle",
        ),
    )

    for modul_kodu, islem in modul_islemleri:
        response = client.post(
            "/api/v2/modul-islemleri/sec",
            json={
                "modul_kodu":
                    modul_kodu,
                "islem":
                    islem,
                "kaynak":
                    "test",
            },
        )

        assert response.status_code == 200

    response = client.get(
        "/api/v2/modul-islemleri/gecmis"
    )

    assert response.status_code == 200

    veri = response.json()

    assert veri["toplam"] == 2
    assert veri["sinir"] == 100
    assert len(veri["kayitlar"]) == 2
    assert (
        veri["kayitlar"][0]["islem"]
        == modul_islemleri[-1][1]
    )


def test_action_history_can_be_cleared():
    client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "rapor",
            "islem": "Yeni rapor olu\u015ftur",
        },
    )

    response = client.delete(
        "/api/v2/modul-islemleri/gecmis"
    )

    veri = response.json()

    assert veri["basarili"] is True
    assert veri["silinen"] == 1
    assert veri["toplam"] == 0


def test_empty_action_is_recorded():
    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "analiz",
            "islem": "   ",
        },
    )

    sonuc = response.json()

    assert sonuc["basarili"] is False
    assert sonuc["islem"] == ""

    history = client.get(
        "/api/v2/modul-islemleri/gecmis"
    ).json()

    assert history["toplam"] == 1
