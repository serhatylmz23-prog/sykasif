from terminal_v2.desktop.runtime_client import (
    DEFAULT_BASE_URL,
    RuntimeClient,
    normalize_base_url,
)


def test_default_base_url():
    assert normalize_base_url("") == DEFAULT_BASE_URL


def test_base_url_adds_http_scheme():
    assert (
        normalize_base_url("192.168.1.10:8013/")
        == "http://192.168.1.10:8013"
    )


def test_runtime_client_routes():
    client = RuntimeClient(
        "127.0.0.1:8013"
    )

    assert client.base_url == (
        "http://127.0.0.1:8013"
    )


def test_desktop_turkish_interface_source():
    from pathlib import Path

    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    required = {
        "Windows Masaüstü Çalışma Alanı",
        "Canlı Modüller",
        "Çalışma alanına bağlanılıyor",
        "Aktif çalışma modülü",
    }

    assert all(
        item in text
        for item in required
    )
