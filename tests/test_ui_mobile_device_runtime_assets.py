from pathlib import Path


STATIC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_telefon_tablet_runtime_varliklari():
    javascript = (
        STATIC
        / "js"
        / "mobile_device_runtime.js"
    )

    stylesheet = (
        STATIC
        / "css"
        / "mobile_device_runtime.css"
    )

    index = (
        STATIC
        / "index.html"
    )

    assert javascript.is_file()
    assert stylesheet.is_file()

    js_text = javascript.read_text(
        encoding="utf-8"
    )

    css_text = stylesheet.read_text(
        encoding="utf-8"
    )

    html = index.read_text(
        encoding="utf-8"
    )

    assert (
        "SyKMobileRuntime"
        in js_text
    )

    assert (
        "enterFullscreen"
        in js_text
    )

    assert (
        "keepAwake"
        in js_text
    )

    assert (
        "SyKaşif Telefonu"
        in js_text
    )

    assert (
        "SyKaşif Tableti"
        in js_text
    )

    assert (
        "data-syk-device-type"
        in css_text
    )

    assert (
        "--syk-safe-bottom"
        in css_text
    )

    assert (
        "mobile_device_runtime.js"
        in html
    )

    assert (
        "mobile_device_runtime.css"
        in html
    )