from pathlib import Path


def kaynak() -> str:
    return Path(
        "terminal_v2/pwa/pwa.js"
    ).read_text(
        encoding="utf-8-sig",
    )


def test_runtime_event_updates_active_module():
    text = kaynak()

    assert (
        "sykasif:runtime-guncellendi"
        in text
    )
    assert "aktifModuluUygula" in text
    assert "aktifModulKodunuCikar" in text


def test_active_module_header_is_updated():
    text = kaynak()

    assert (
        'document.getElementById('
        in text
    )
    assert '"aktifModul"' in text
    assert (
        "`Aktif mod?l: ${modulKodu}`"
        in text
    )


def test_active_module_card_state_is_updated():
    text = kaynak()

    assert "[data-modul-kodu]" in text
    assert "classList.toggle(" in text
    assert '"aria-current"' in text
    assert '"?al???yor"' in text
    assert '"Bekliyor"' in text


def test_active_module_update_dispatches_event():
    text = kaynak()

    assert (
        "sykasif:aktif-modul-guncellendi"
        in text
    )
    assert "CustomEvent(" in text
