from pathlib import Path


def kaynak() -> str:
    return Path(
        "terminal_v2/pwa/pwa.js"
    ).read_text(
        encoding="utf-8-sig",
    )


def test_active_module_event_updates_detail_panel():
    text = kaynak()

    assert (
        "sykasif:aktif-modul-guncellendi"
        in text
    )
    assert (
        "aktifModulDetayiniUygula"
        in text
    )


def test_active_module_detail_uses_shared_catalog():
    text = kaynak()

    assert "katalog.modulGetir" in text
    assert "event.detail?.aktif_modul" in text


def test_active_module_detail_updates_content():
    text = kaynak()

    assert '"modulBasligi"' in text
    assert '"modulAciklamasi"' in text
    assert '"islemAlani"' in text
    assert "modul.baslik" in text
    assert "modul.aciklama" in text


def test_active_module_detail_rebuilds_actions():
    text = kaynak()

    assert "modul.islemler" in text
    assert 'document.createElement(' in text
    assert '"button"' in text
    assert "modul-islem-butonu" in text
    assert "??lem se?ildi:" in text
