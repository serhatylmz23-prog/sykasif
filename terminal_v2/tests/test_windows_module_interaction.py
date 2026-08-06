from pathlib import Path

from terminal_v2.desktop.runtime_client import (
    RuntimeClient,
)


def test_desktop_client_has_active_module_method():
    client = RuntimeClient()

    assert callable(
        client.aktif_modulu_degistir
    )


def test_desktop_client_has_module_status_method():
    client = RuntimeClient()

    assert callable(
        client.modul_durumunu_degistir
    )


def test_desktop_cards_are_clickable():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert 'cursor="hand2"' in text
    assert 'bind("<Button-1>"' in text
    assert "_activate_module" in text

    assert (
        "A\u00e7mak i\u00e7in t\u0131klay\u0131n"
        in text
    )

    assert (
        "Mod\u00fcl a\u00e7\u0131l\u0131yor..."
        in text
    )


def test_desktop_uses_runtime_module_api():
    text = Path(
        "terminal_v2/desktop/runtime_client.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert (
        "/api/v2/modul-kartlari/aktif"
        in text
    )

    assert (
        "/api/v2/modul-kartlari/durum"
        in text
    )
