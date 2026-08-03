from pathlib import Path


STATIC_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_dinamik_ortam_varliklari():
    javascript = (
        STATIC_ROOT
        / "js"
        / "adaptive_environment.js"
    )

    stylesheet = (
        STATIC_ROOT
        / "css"
        / "adaptive_environment.css"
    )

    index = STATIC_ROOT / "index.html"

    assert javascript.is_file()
    assert stylesheet.is_file()

    js_text = javascript.read_text(
        encoding="utf-8"
    )

    css_text = stylesheet.read_text(
        encoding="utf-8"
    )

    index_text = index.read_text(
        encoding="utf-8"
    )

    assert "AmbientLightSensor" in js_text
    assert "recommended_brightness" in js_text
    assert "sykWeather" in js_text
    assert "syk-weather-rain" in css_text
    assert "syk-weather-snow" in css_text
    assert "syk-weather-fog" in css_text
    assert "adaptive_environment.js" in index_text
    assert "adaptive_environment.css" in index_text