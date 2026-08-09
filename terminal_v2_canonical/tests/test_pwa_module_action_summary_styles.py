from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def css_source() -> str:
    response = client.get(
        "/pwa/pwa.css"
    )

    assert response.status_code == 200

    return response.text


def test_module_action_summary_has_grid():
    text = css_source()

    assert ".modul-islem-ozeti {" in text
    assert "display: grid" in text
    assert "repeat(" in text


def test_summary_total_has_distinct_style():
    text = css_source()

    assert (
        '.modul-islem-ozeti '
        '[data-ozet="toplam"]'
        in text
    )

    assert "#a9d3f3" in text


def test_summary_success_has_distinct_style():
    text = css_source()

    assert (
        '.modul-islem-ozeti '
        '[data-ozet="basarili"]'
        in text
    )

    assert "#55e6c1" in text


def test_summary_error_has_distinct_style():
    text = css_source()

    assert (
        '.modul-islem-ozeti '
        '[data-ozet="hatali"]'
        in text
    )

    assert "#ff8585" in text


def test_summary_is_mobile_responsive():
    text = css_source()

    assert "@media (max-width: 720px)" in text
    assert "grid-template-columns: 1fr" in text
    assert "justify-content: flex-start" in text


def test_summary_supports_high_contrast():
    text = css_source()

    assert (
        "@media (prefers-contrast: more)"
        in text
    )

    assert "border-width: 2px" in text
