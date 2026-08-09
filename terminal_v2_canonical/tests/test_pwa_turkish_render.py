from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_pwa_index_has_ascii_safe_turkish():
    response = client.get("/pwa/")

    assert response.status_code == 200
    assert "SyKa&#351;if Terminal V2" in response.text
    assert (
        "Canl&#305; &#199;al&#305;&#351;ma Alan&#305;"
        in response.text
    )


def test_pwa_manifest_has_correct_turkish_name():
    response = client.get(
        "/pwa/manifest.webmanifest"
    )

    assert response.status_code == 200

    manifest = response.json()

    assert manifest["name"] == "SyKa\u015fif Terminal V2"
    assert manifest["short_name"] == "SyKa\u015fif"


def test_pwa_cache_version_is_updated():
    response = client.get(
        "/pwa/service-worker.js"
    )

    assert response.status_code == 200
    assert "sykasif-pwa-v2" in response.text
