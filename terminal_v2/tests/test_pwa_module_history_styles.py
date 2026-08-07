from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def css_source() -> str:
    response = client.get(
        "/pwa/pwa.css"
    )

    assert response.status_code == 200

    return response.text


def test_module_history_panel_has_styles():
    text = css_source()

    assert ".modul-islem-gecmisi {" in text
    assert ".modul-islem-gecmisi-baslik {" in text
    assert ".modul-islem-gecmisi-liste {" in text


def test_module_history_records_have_status_styles():
    text = css_source()

    assert (
        '.modul-islem-gecmisi-kaydi'
        '[data-durum="basarili"]'
        in text
    )

    assert (
        '.modul-islem-gecmisi-kaydi'
        '[data-durum="hata"]'
        in text
    )

    assert "#55e6c1" in text
    assert "#ff6b6b" in text


def test_module_history_clear_button_is_accessible():
    text = css_source()

    assert (
        ".modul-islem-gecmisi-temizle"
        in text
    )

    assert ":focus-visible" in text
    assert "cursor: pointer" in text


def test_module_history_is_mobile_responsive():
    text = css_source()

    assert "@media (max-width: 720px)" in text
    assert "flex-direction: column" in text
    assert "width: 100%" in text


def test_module_history_respects_reduced_motion():
    text = css_source()

    assert (
        "@media (prefers-reduced-motion: reduce)"
        in text
    )

    assert "transition: none" in text
