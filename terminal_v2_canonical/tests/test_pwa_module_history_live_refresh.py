from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def history_source() -> str:
    response = client.get(
        "/pwa/module_history.js"
    )

    assert response.status_code == 200

    return response.text


def test_history_refreshes_periodically():
    text = history_source()

    assert "YENILEME_ARALIGI_MS = 5000" in text
    assert "window.setInterval(" in text
    assert "guvenliGecmisYenile" in text


def test_history_stops_when_page_is_hidden():
    text = history_source()

    assert "document.hidden" in text
    assert '"visibilitychange"' in text
    assert "canliYenilemeyiDurdur" in text
    assert "window.clearInterval(" in text


def test_history_recovers_when_connection_returns():
    text = history_source()

    assert '"online"' in text
    assert '"offline"' in text
    assert "canliYenilemeyiBaslat" in text


def test_history_timer_is_cleaned_before_unload():
    text = history_source()

    assert '"beforeunload"' in text
    assert (
        'window.addEventListener('
        in text
    )


def test_history_live_controller_is_exposed():
    text = history_source()

    assert (
        "window.SyKasifModuleHistoryLive"
        in text
    )
    assert "yenilemeAraligi" in text
