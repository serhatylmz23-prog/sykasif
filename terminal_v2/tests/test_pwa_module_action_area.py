from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_pwa_has_shared_module_content_targets():
    response = client.get("/pwa/")

    assert response.status_code == 200
    assert 'id="modulBasligi"' in response.text
    assert 'id="modulAciklamasi"' in response.text
    assert 'id="islemAlani"' in response.text


def test_pwa_has_module_action_styles():
    response = client.get(
        "/pwa/pwa.css"
    )

    assert response.status_code == 200
    assert ".modul-islem-alani" in response.text
    assert ".modul-islem-butonu" in response.text


def test_pwa_action_area_is_mobile_responsive():
    response = client.get(
        "/pwa/pwa.css"
    )

    assert "@media (max-width: 640px)" in (
        response.text
    )
    assert "grid-template-columns: 1fr" in (
        response.text
    )
