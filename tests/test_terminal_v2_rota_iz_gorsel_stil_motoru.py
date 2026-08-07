from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_gorsel_stil_motoru.js"
)


def source():
    assert JS.exists(), f"Eksik dosya: {JS}"
    return JS.read_text(encoding="utf-8")


def test_stil_motoru_dosyasi_var():
    assert JS.exists()


def test_rota_ve_iz_turleri_var():
    text = source()
    assert 'ROTA: "rota"' in text
    assert 'IZ: "iz"' in text


def test_durum_sozlesmesi_var():
    text = source()
    assert 'NORMAL: "normal"' in text
    assert 'AKTIF: "aktif"' in text
    assert 'SECILI: "secili"' in text
    assert 'UYARI: "uyari"' in text
    assert 'TAMAMLANDI: "tamamlandi"' in text


def test_rota_ve_iz_stilleri_ayri():
    text = source()
    assert "rota: Object.freeze({" in text
    assert "iz: Object.freeze({" in text
    assert "dash: Object.freeze([5, 7])" in text


def test_ana_stil_uretici_var():
    text = source()
    assert "export function createRouteTraceStyle" in text
    assert "assertKind(kind)" in text
    assert "assertState(state)" in text


def test_rota_ve_iz_kisa_ureticileri_var():
    text = source()
    assert "export function createRouteStyle" in text
    assert "export function createTraceStyle" in text


def test_yogunluk_sinirlandirmasi_var():
    text = source()
    assert "function clamp" in text
    assert "0.5" in text
    assert "2," in text


def test_canli_durum_bayraklari_var():
    text = source()
    assert "selected:" in text
    assert "warning:" in text
    assert "completed:" in text
    assert "motion:" in text


def test_segment_gorsel_durumu_var():
    text = source()
    assert "export function createSegmentVisualState" in text
    assert "segmentIndex:" in text
    assert "drawable:" in text
