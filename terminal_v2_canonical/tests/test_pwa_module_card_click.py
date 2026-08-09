from pathlib import Path


def kaynak() -> str:
    return Path(
        "terminal_v2/pwa/pwa.js"
    ).read_text(
        encoding="utf-8-sig",
    )


def test_pwa_module_cards_use_active_module_api():
    text = kaynak()

    assert (
        '"/api/v2/modul-kartlari/aktif"'
        in text
    )
    assert "aktifModuluDegistir" in text


def test_pwa_module_cards_are_clickable():
    text = kaynak()

    assert "[data-modul-kodu]" in text
    assert '"click"' in text
    assert '"keydown"' in text
    assert '"Enter"' in text


def test_pwa_module_change_dispatches_runtime_event():
    text = kaynak()

    assert (
        '"sykasif:runtime-guncellendi"'
        in text
    )
    assert "CustomEvent(" in text


def test_pwa_module_cards_have_accessibility_state():
    text = kaynak()

    assert '"role"' in text
    assert '"button"' in text
    assert '"tabindex"' in text
    assert '"aria-busy"' in text
