from pathlib import Path


STATIC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_kasif_ikon_varliklari():
    manifest = (
        STATIC
        / "icons"
        / "kasif"
        / "icons.json"
    )

    javascript = (
        STATIC
        / "js"
        / "kasif_icon_runtime.js"
    )

    stylesheet = (
        STATIC
        / "css"
        / "kasif_icon_runtime.css"
    )

    index = (
        STATIC
        / "index.html"
    )

    assert manifest.is_file()
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

    manifest_text = (
        manifest.read_text(
            encoding="utf-8"
        )
    )

    assert (
        "SyKKasifIcons"
        in js_text
    )

    assert (
        "renderGrid"
        in js_text
    )

    assert (
        ".syk-kasif-icon"
        in css_text
    )

    assert (
        "data-icon-id"
        in css_text
    )

    assert (
        '"display_name": "Kaşif"'
        in manifest_text
    )

    assert (
        '"headphones": false'
        in manifest_text
    )

    assert (
        "kasif_icon_runtime.js"
        in html
    )

    assert (
        "kasif_icon_runtime.css"
        in html
    )