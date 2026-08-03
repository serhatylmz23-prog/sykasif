from pathlib import Path


ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_dtse_dikkat_gorsel_katman_varliklari():
    javascript = (
        ROOT
        / "js"
        / "dtse_attention_overlay.js"
    )

    stylesheet = (
        ROOT
        / "css"
        / "dtse_attention_overlay.css"
    )

    index = ROOT / "index.html"

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

    assert "SyKDTSEAttention" in js_text
    assert "crescent" not in js_text.lower()
    assert "dtse-attention-overlay" in js_text
    assert "/api/syk-ui/dtse/live" in js_text

    assert "dtse-attention-card" in css_text
    assert "dtse-overlay-pulse" in css_text

    assert (
        "dtse_attention_overlay.js"
        in index_text
    )

    assert (
        "dtse_attention_overlay.css"
        in index_text
    )