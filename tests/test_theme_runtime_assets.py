from pathlib import Path


STATIC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_tema_runtime_varliklari():
    js = (
        STATIC
        / "js"
        / "theme_runtime.js"
    )

    css = (
        STATIC
        / "css"
        / "theme_runtime.css"
    )

    index = STATIC / "index.html"

    assert js.is_file()
    assert css.is_file()

    assert "SyKThemeRuntime" in js.read_text(
        encoding="utf-8"
    )

    assert "--syk-theme-accent" in css.read_text(
        encoding="utf-8"
    )

    html = index.read_text(
        encoding="utf-8"
    )

    assert "theme_runtime.js" in html
    assert "theme_runtime.css" in html