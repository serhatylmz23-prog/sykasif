from pathlib import Path


STATIC_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_dtse_bilimsel_runtime_varliklari():
    javascript = (
        STATIC_ROOT
        / "js"
        / "dtse_evidence_scientific_runtime.js"
    )

    stylesheet = (
        STATIC_ROOT
        / "css"
        / "dtse_evidence_scientific_runtime.css"
    )

    index = STATIC_ROOT / "index.html"

    assert javascript.is_file()
    assert stylesheet.is_file()
    assert index.is_file()

    js_text = javascript.read_text(
        encoding="utf-8"
    )

    css_text = stylesheet.read_text(
        encoding="utf-8"
    )

    index_text = index.read_text(
        encoding="utf-8"
    )

    assert (
        "SyKDTSEScientificRuntime"
        in js_text
    )

    assert (
        "/scientific-modules"
        in js_text
    )

    assert (
        "scientific-modules/"
        in js_text
    )

    assert (
        "live_value"
        in js_text
    )

    assert (
        "confidence"
        in js_text
    )

    assert (
        "activeSockets"
        in js_text
    )

    assert (
        "dtse-scientific-live-card"
        in css_text
    )

    assert (
        "dtse-scientific-runtime-view"
        in css_text
    )

    assert (
        "dtse_evidence_scientific_runtime.css"
        in index_text
    )

    assert (
        "dtse_evidence_scientific_runtime.js"
        in index_text
    )