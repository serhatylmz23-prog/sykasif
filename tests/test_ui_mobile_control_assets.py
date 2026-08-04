from pathlib import Path


STATIC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_mobil_kontrol_paneli_varliklari():
    javascript = (
        STATIC
        / "js"
        / "mobile_control_panel.js"
    )

    stylesheet = (
        STATIC
        / "css"
        / "mobile_control_panel.css"
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
        "SyKMobileControl"
        in js_text
    )

    assert (
        "Bildirim İzni"
        in js_text
    )

    assert (
        "Cihaz Eşleştir"
        in js_text
    )

    assert (
        "Verileri Eşitle"
        in js_text
    )

    assert (
        "Ekranı Açık Tut"
        in js_text
    )

    assert (
        "SyKMobileSensors"
        in js_text
    )

    assert (
        "SyKMobileOffline"
        in js_text
    )

    assert (
        ".syk-mobile-control-panel"
        in css_text
    )

    assert (
        "mobile_control_panel.js"
        in html
    )

    assert (
        "mobile_control_panel.css"
        in html
    )