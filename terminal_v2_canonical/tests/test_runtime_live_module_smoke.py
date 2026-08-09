from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_runtime_health_is_available():
    response = client.get(
        "/api/v2/runtime-state"
    )

    assert response.status_code == 200

    veri = response.json()

    assert isinstance(veri, dict)


def test_module_catalog_is_available():
    response = client.get(
        "/api/v2/modul-katalogu"
    )

    assert response.status_code == 200

    moduller = response.json()

    assert isinstance(moduller, list)
    assert len(moduller) >= 7

    kodlar = {
        modul["kod"]
        for modul in moduller
    }

    assert {
        "dashboard",
        "harita",
        "kanit",
        "analiz",
        "gorev",
        "rapor",
        "sensorler",
    }.issubset(kodlar)


def test_each_module_detail_is_available():
    moduller = client.get(
        "/api/v2/modul-katalogu"
    ).json()

    for modul in moduller:
        response = client.get(
            "/api/v2/modul-katalogu/"
            + modul["kod"]
        )

        assert response.status_code == 200

        detay = response.json()

        assert detay["kod"] == modul["kod"]
        assert detay["baslik"]
        assert detay["aciklama"]
        assert detay["islemler"]


def test_module_action_end_to_end_flow():
    client.delete(
        "/api/v2/modul-islemleri/gecmis"
    )

    modul = client.get(
        "/api/v2/modul-katalogu/rapor"
    ).json()

    islem = modul["islemler"][0]

    response = client.post(
        "/api/v2/modul-islemleri/sec",
        json={
            "modul_kodu": "rapor",
            "islem": islem,
            "kaynak": "smoke-test",
        },
    )

    assert response.status_code == 200

    sonuc = response.json()

    assert sonuc["basarili"] is True
    assert sonuc["modul_kodu"] == "rapor"
    assert sonuc["islem"] == islem
    assert sonuc["kaynak"] == "smoke-test"

    gecmis = client.get(
        "/api/v2/modul-islemleri/gecmis"
    ).json()

    assert gecmis["toplam"] == 1
    assert gecmis["kayitlar"][0]["islem"] == islem

    ozet = client.get(
        "/api/v2/modul-islemleri/ozet"
    ).json()

    assert ozet["toplam"] == 1
    assert ozet["basarili"] == 1
    assert ozet["hatali"] == 0


def test_pwa_runtime_assets_are_available():
    yollar = (
        "/pwa/",
        "/pwa/pwa.css",
        "/pwa/pwa.js",
        "/pwa/module_catalog.js",
        "/pwa/module_actions.js",
        "/pwa/module_history.js",
        "/pwa/manifest.webmanifest",
        "/pwa/service-worker.js",
    )

    for yol in yollar:
        response = client.get(
            yol
        )

        assert response.status_code == 200
        assert response.content


def test_pwa_index_loads_live_runtime_assets():
    response = client.get(
        "/pwa/"
    )

    assert response.status_code == 200

    text = response.text

    assert "./pwa.js" in text
    assert "./module_catalog.js" in text
    assert "./module_actions.js" in text
    assert "./module_history.js" in text
    assert "./manifest.webmanifest" in text


def test_mobile_short_route_redirects_to_pwa():
    response = client.get(
        "/mobil",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "/pwa/"
