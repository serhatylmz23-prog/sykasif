from pathlib import Path


STATIC_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_dtse_kanit_odak_varliklari():
    javascript = (
        STATIC_ROOT
        / "js"
        / "dtse_evidence_focus.js"
    )

    stylesheet = (
        STATIC_ROOT
        / "css"
        / "dtse_evidence_focus.css"
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

    assert "SyKDTSEEvidenceFocus" in js_text
    assert "data-dtse-focus-tab" in js_text
    assert "surface" in js_text
    assert "geometry" in js_text
    assert "thermal" in js_text
    assert "spectral" in js_text

    assert (
        "dtse-evidence-stage-focused"
        in css_text
    )

    assert (
        "dtse-evidence-focus-panel"
        in css_text
    )

    assert (
        "dtse_evidence_focus.css"
        in index_text
    )

    assert (
        "dtse_evidence_focus.js"
        in index_text
    )