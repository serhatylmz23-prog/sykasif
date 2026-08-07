from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "terminal_v2" / "static" / "js" / "rota_iz_cizgi_geometrisi.js"


def source():
    assert JS.exists(), f"Eksik dosya: {JS}"
    return JS.read_text(encoding="utf-8")


def test_rota_iz_geometri_dosyasi_var():
    assert JS.exists()


def test_nokta_normalizasyonu_var():
    text = source()
    assert "export function normalizePoint" in text
    assert "Number.isFinite" in text


def test_tekrar_nokta_temizligi_var():
    text = source()
    assert "export function normalizePoints" in text
    assert "previous.x === point.x" in text
    assert "previous.y === point.y" in text


def test_segment_geometrisi_var():
    text = source()
    assert "export function buildSegments" in text
    assert "export function segmentLength" in text
    assert "Math.hypot" in text


def test_toplam_uzunluk_var():
    text = source()
    assert "export function totalLength" in text


def test_bounds_ve_merkez_var():
    text = source()
    assert "export function bounds" in text
    assert "center:" in text
    assert "width:" in text
    assert "height:" in text


def test_rota_ve_iz_turleri_destekleniyor():
    text = source()
    assert 'kind = "rota"' in text
    assert 'kind !== "rota" && kind !== "iz"' in text


def test_cizilebilirlik_durumu_var():
    text = source()
    assert "drawable: normalized.length >= 2" in text
    assert "empty: normalized.length === 0" in text
