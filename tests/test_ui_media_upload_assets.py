from pathlib import Path


STATIC_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_media_yukleme_panel_varliklari():
    javascript = (
        STATIC_ROOT
        / "js"
        / "media_upload_panel.js"
    )

    stylesheet = (
        STATIC_ROOT
        / "css"
        / "media_upload_panel.css"
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

    assert "SyKMediaUpload" in js_text

    assert (
        "/media-analysis"
        in js_text
    )

    assert (
        "syk-media-upload-panel"
        in css_text
    )

    assert (
        "media_upload_panel.js"
        in index_text
    )

    assert (
        "media_upload_panel.css"
        in index_text
    )