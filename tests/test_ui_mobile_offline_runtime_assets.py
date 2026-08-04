from pathlib import Path


STATIC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_cevrimdisi_runtime_varliklari():
    javascript = (
        STATIC
        / "js"
        / "mobile_offline_runtime.js"
    )

    stylesheet = (
        STATIC
        / "css"
        / "mobile_offline_runtime.css"
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
        "SyKMobileOffline"
        in js_text
    )

    assert (
        "indexedDB"
        in js_text
    )

    assert (
        "createPairing"
        in js_text
    )

    assert (
        "confirmPairing"
        in js_text
    )

    assert (
        "offline_queue"
        in js_text
    )

    assert (
        "Çevrimdışı"
        in css_text
    )

    assert (
        "Veriler eşitleniyor"
        in css_text
    )

    assert (
        "mobile_offline_runtime.js"
        in html
    )

    assert (
        "mobile_offline_runtime.css"
        in html
    )