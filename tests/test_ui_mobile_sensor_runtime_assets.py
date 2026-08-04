from pathlib import Path


STATIC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_mobil_sensor_varliklari():
    javascript = (
        STATIC
        / "js"
        / "mobile_sensor_runtime.js"
    )

    stylesheet = (
        STATIC
        / "css"
        / "mobile_sensor_runtime.css"
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
        "SyKMobileSensors"
        in js_text
    )

    assert (
        "startCamera"
        in js_text
    )

    assert (
        "startMicrophone"
        in js_text
    )

    assert (
        "requestLocation"
        in js_text
    )

    assert (
        "syk:media-analysis-requested"
        in js_text
    )

    assert (
        ".syk-mobile-sensor-panel"
        in css_text
    )

    assert (
        "mobile_sensor_runtime.js"
        in html
    )

    assert (
        "mobile_sensor_runtime.css"
        in html
    )