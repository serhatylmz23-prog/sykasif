from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_canli_renderer.js"
)


def source():
    assert JS.exists()
    return JS.read_text(encoding="utf-8")


def test_renderer_dosyasi_var():
    assert JS.exists()


def test_birlesik_sozlesme_renderer_bagli():
    text = source()
    assert "createLiveRouteTraceContract" in text
    assert "updateLiveRouteTraceFrame" in text
    assert "isLiveRouteTraceContract" in text
    assert 'from "./rota_iz_canli_gorsel_sozlesmesi.js"' in text


def test_svg_path_uretimi_var():
    text = source()
    assert 'createSvgElement("path")' in text
    assert 'document.createElementNS' in text


def test_geometri_path_donusumu_var():
    text = source()
    assert "function pointsToPath" in text
    assert 'index === 0 ? "M" : "L"' in text


def test_canli_renderer_factory_var():
    text = source()
    assert "export function createLiveRouteTraceRenderer" in text
    assert "svgRoot.appendChild(path)" in text


def test_hareket_frame_renderer_bagli():
    text = source()
    assert "function render(elapsedMs = 0)" in text
    assert "updateLiveRouteTraceFrame" in text
    assert '"stroke-dashoffset"' in text


def test_durum_degistirme_var():
    text = source()
    assert "function setState(nextState)" in text
    assert "state: nextState" in text


def test_renderer_temizleme_var():
    text = source()
    assert "function destroy()" in text
    assert "removeChild(path)" in text


def test_renderer_sozlesme_dogrulama_var():
    text = source()
    assert "isValid()" in text
    assert "isLiveRouteTraceContract(contract)" in text


def test_dom_veri_sozlesmesi_var():
    text = source()
    assert '"data-syk-route-trace"' in text
    assert "path.dataset.sykRouteState" in text
    assert "path.dataset.sykRouteDrawable" in text
