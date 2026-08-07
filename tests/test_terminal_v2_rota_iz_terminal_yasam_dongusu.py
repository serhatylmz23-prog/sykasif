from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_terminal_yasam_dongusu.js"
)


def source():
    assert JS.exists()
    return JS.read_text(encoding="utf-8")


def test_yasam_dongusu_dosyasi_var():
    assert JS.exists()


def test_ekran_koprusu_bagli():
    text = source()
    assert "findRouteTraceContainer" in text
    assert "mountRouteTraceLayer" in text
    assert 'from "./rota_iz_terminal_ekran_koprusu.js"' in text


def test_tek_aktif_runtime_sozlesmesi_var():
    text = source()
    assert "let activeRuntime = null" in text
    assert "if (activeRuntime)" in text


def test_terminal_mount_var():
    text = source()
    assert "export function mountTerminalRouteTrace" in text
    assert "findRouteTraceContainer(root)" in text
    assert "mountRouteTraceLayer({" in text


def test_unmount_var():
    text = source()
    assert "export function unmountTerminalRouteTrace" in text
    assert "activeRuntime.destroy()" in text
    assert "activeRuntime = null" in text


def test_domcontentloaded_boot_var():
    text = source()
    assert 'document.readyState === "loading"' in text
    assert '"DOMContentLoaded"' in text
    assert "{ once: true }" in text


def test_pagehide_temizleme_var():
    text = source()
    assert '"pagehide"' in text
    assert "unmountTerminalRouteTrace" in text


def test_runtime_erisim_var():
    text = source()
    assert "export function getTerminalRouteTraceRuntime" in text


def test_lifecycle_binding_var():
    text = source()
    assert "export function bindTerminalRouteTraceLifecycle" in text
    assert "bootTerminalRouteTrace(options)" in text


def test_default_rota_noktalari_var():
    text = source()
    assert "function defaultRoutePoints()" in text
    assert "{ x: 120, y: 760 }" in text
    assert "{ x: 860, y: 240 }" in text
