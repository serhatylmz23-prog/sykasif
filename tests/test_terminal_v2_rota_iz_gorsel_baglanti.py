from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

JS = ROOT / "terminal_v2" / "static" / "js"

GEOMETRY = JS / "rota_iz_cizgi_geometrisi.js"
STYLE = JS / "rota_iz_gorsel_stil_motoru.js"
BRIDGE = JS / "rota_iz_gorsel_baglanti.js"


def source():
    assert BRIDGE.exists()
    return BRIDGE.read_text(encoding="utf-8")


def test_motor_dosyalari_var():
    assert GEOMETRY.exists()
    assert STYLE.exists()
    assert BRIDGE.exists()


def test_geometri_motoru_gercek_kaynaktan_import_ediliyor():
    text = source()
    assert 'from "./rota_iz_cizgi_geometrisi.js"' in text
    assert "GeometryEngine" in text


def test_stil_motoru_import_ediliyor():
    text = source()
    assert 'from "./rota_iz_gorsel_stil_motoru.js"' in text
    assert "createRouteTraceStyle" in text


def test_geometri_normalizasyonu_var():
    text = source()
    assert "function normalizeGeometryResult" in text
    assert "points.length >= 2" in text


def test_ana_gorsel_sozlesme_var():
    text = source()
    assert "export function createRouteTraceVisual" in text
    assert "geometry: normalizedGeometry" in text
    assert "style," in text


def test_rota_ureticisi_var():
    assert "export function createRouteVisual" in source()


def test_iz_ureticisi_var():
    assert "export function createTraceVisual" in source()


def test_cizilebilirlik_var():
    text = source()
    assert "drawable: normalizedGeometry.drawable" in text
