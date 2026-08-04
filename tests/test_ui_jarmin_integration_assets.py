from pathlib import Path


STATIC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_jarmin_entegrasyon_varligi():
    script = (
        STATIC
        / "js"
        / "jarmin_integration.js"
    )

    index = (
        STATIC
        / "index.html"
    )

    assert script.is_file()

    text = script.read_text(
        encoding="utf-8"
    )

    html = index.read_text(
        encoding="utf-8"
    )

    assert (
        "SyKJarminIntegration"
        in text
    )

    assert (
        "syk:dtse-attention"
        in text
    )

    assert (
        "syk:sealed-report-created"
        in text
    )

    assert (
        "jarmin_integration.js"
        in html
    )