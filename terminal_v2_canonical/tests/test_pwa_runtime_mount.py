from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_pwa_index_is_served():
    from html import unescape

    response = client.get("/pwa/")

    assert response.status_code == 200

    rendered = unescape(
        response.text
    )

    assert "SyKa\u015fif Terminal V2" in rendered
    assert (
        "Canl\u0131 \u00c7al\u0131\u015fma Alan\u0131"
        in rendered
    )
    assert 'lang="tr"' in response.text


def test_pwa_manifest_is_served():
    response = client.get(
        "/pwa/manifest.webmanifest"
    )

    assert response.status_code == 200

    manifest = response.json()

    assert manifest["short_name"] == "SyKa\u015fif"
    assert manifest["display"] == "standalone"
    assert manifest["lang"] == "tr"


def test_mobile_route_redirects_to_pwa():
    response = client.get(
        "/mobil",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "/pwa/"


def test_service_worker_is_served():
    response = client.get(
        "/pwa/service-worker.js"
    )

    assert response.status_code == 200
    assert "CACHE_NAME" in response.text
