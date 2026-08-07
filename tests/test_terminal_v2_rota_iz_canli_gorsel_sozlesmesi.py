from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_canli_gorsel_sozlesmesi.js"
)


def source():
    assert JS.exists()
    return JS.read_text(encoding="utf-8")


def test_birlesik_sozlesme_dosyasi_var():
    assert JS.exists()


def test_geometri_motoru_bagli():
    text = source()
    assert "normalizeRouteTraceGeometry" in text
    assert 'from "./rota_iz_cizgi_geometrisi.js"' in text


def test_stil_motoru_bagli():
    text = source()
    assert "createRouteTraceVisual" in text
    assert 'from "./rota_iz_gorsel_stil_motoru.js"' in text


def test_hareket_motoru_bagli():
    text = source()
    assert "applyMotionToVisual" in text
    assert 'from "./rota_iz_canli_hareket_motoru.js"' in text


def test_sozlesme_surumu_var():
    text = source()
    assert 'ROUTE_TRACE_CONTRACT_VERSION = "1.0.0"' in text


def test_canli_sozlesme_uretici_var():
    text = source()
    assert "export function createLiveRouteTraceContract" in text
    assert 'contract: "SYK_ROUTE_TRACE_LIVE_VISUAL"' in text
    assert "geometry:" in text
    assert "style:" in text
    assert "motion:" in text


def test_drawable_kurali_var():
    text = source()
    assert "geometry.points.length >= 2" in text


def test_frame_guncelleme_var():
    text = source()
    assert "export function updateLiveRouteTraceFrame" in text
    assert "elapsedMs" in text


def test_sozlesme_dogrulayici_var():
    text = source()
    assert "export function isLiveRouteTraceContract" in text
    assert "SYK_ROUTE_TRACE_LIVE_VISUAL" in text
