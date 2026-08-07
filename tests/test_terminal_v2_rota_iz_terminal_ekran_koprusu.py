from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_terminal_ekran_koprusu.js"
)


def source():
    assert JS.exists()
    return JS.read_text(encoding="utf-8")


def test_ekran_koprusu_var():
    assert JS.exists()


def test_renderer_bagli():
    text = source()
    assert "createLiveRouteTraceRenderer" in text
    assert 'from "./rota_iz_canli_renderer.js"' in text


def test_svg_canli_katman_var():
    text = source()
    assert 'ROUTE_TRACE_LAYER_ID' in text
    assert '"syk-route-trace-layer"' in text
    assert '"data-syk-live-route-layer"' in text


def test_terminal_mount_var():
    text = source()
    assert "export function mountRouteTraceLayer" in text
    assert "createSvgLayer(container)" in text


def test_animation_frame_var():
    text = source()
    assert "requestAnimationFrame(frame)" in text
    assert "cancelAnimationFrame" in text


def test_renderer_frame_bagli():
    text = source()
    assert "renderer.render(" in text
    assert "timestamp - startedAt" in text


def test_baslat_durdur_var():
    text = source()
    assert "function start()" in text
    assert "function stop()" in text
    assert "isRunning()" in text


def test_durum_degistirme_bagli():
    text = source()
    assert "function setState(nextState)" in text
    assert "renderer.setState(" in text


def test_temizleme_var():
    text = source()
    assert "function destroy()" in text
    assert "renderer.destroy()" in text


def test_terminal_container_bulucu_var():
    text = source()
    assert "export function findRouteTraceContainer" in text
    assert "[data-syk-route-container]" in text
    assert "#syk-ui-screen" in text
