from pathlib import Path


def pwa_source() -> str:
    return Path(
        "terminal_v2/pwa/pwa.js"
    ).read_text(
        encoding="utf-8-sig",
    )


def test_pwa_shared_module_block_exists():
    text = pwa_source()

    assert (
        "SYKASIF_ORTAK_MODUL_GORUNUMU_BASLANGIC"
        in text
    )
    assert (
        "function ortakModulKatalogunuUygula"
        in text
    )


def test_pwa_reads_shared_catalog():
    text = pwa_source()

    assert "window.SyKasifModuleCatalog" in text
    assert "sykasif:modul-katalogu-hazir" in text
    assert "katalogDurumu.moduller" in text


def test_pwa_renders_shared_module_content():
    text = pwa_source()

    assert 'eleman("modulBasligi")' in text
    assert 'eleman("modulAciklamasi")' in text
    assert 'eleman("islemAlani")' in text
    assert "aktifModul.islemler" in text


def test_pwa_builds_clickable_action_buttons():
    text = pwa_source()

    assert 'document.createElement(' in text
    assert '"button"' in text
    assert "modul-islem-butonu" in text
    assert "??lem se?ildi:" in text
