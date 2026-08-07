from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PWA = ROOT / "terminal_v2" / "pwa" / "pwa.js"

ENGINE = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_durum_motoru.js"
)

CSS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "css"
    / "canli_modul_gorsel_durum.css"
)


def pwa_source():
    assert PWA.exists()
    return PWA.read_text(encoding="utf-8")


def engine_source():
    assert ENGINE.exists()
    return ENGINE.read_text(encoding="utf-8")


def css_source():
    assert CSS.exists()
    return CSS.read_text(encoding="utf-8")


def test_pwa_modul_dom_contract():
    text = pwa_source()
    assert "[data-modul-kodu]" in text
    assert "dataset.modulKodu" in text


def test_pwa_aktif_modul_event_contract():
    text = pwa_source()
    assert "aktif_modul" in text
    assert "sykasif:aktif-modul-guncellendi" in text


def test_engine_runtime_durum_kaynagi():
    assert "[data-runtime-durum]" in engine_source()


def test_engine_secim_contract():
    assert "dataset.sykModulSecim" in engine_source()


def test_engine_runtime_contract():
    assert "dataset.sykModulDurum" in engine_source()


def test_engine_hareket_contract():
    assert "dataset.sykModulHareket" in engine_source()


def test_bekliyor_contract():
    assert 'BEKLIYOR: "bekliyor"' in engine_source()
    assert 'data-syk-modul-durum="bekliyor"' in css_source()


def test_calisiyor_contract():
    assert 'CALISIYOR: "calisiyor"' in engine_source()
    assert 'data-syk-modul-durum="calisiyor"' in css_source()


def test_durdu_contract():
    assert 'DURDU: "durdu"' in engine_source()
    assert 'data-syk-modul-durum="durdu"' in css_source()


def test_cevrimdisi_contract():
    assert 'CEVRIMDISI: "cevrimdisi"' in engine_source()
    assert 'data-syk-modul-durum="cevrimdisi"' in css_source()


def test_calisiyor_hareketi_acar():
    text = engine_source()
    assert "runtimeDurum === DURUMLAR.CALISIYOR" in text
    assert 'data-syk-modul-hareket="aktif"' in css_source()


def test_event_yeniden_cizim_contract():
    text = engine_source()
    assert "aktifModulEventiniIsle" in text
    assert "aktifModulGorselDurumunuUygula" in text
