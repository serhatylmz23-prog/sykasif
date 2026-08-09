from pathlib import Path


def test_mousewheel_binding_is_scoped():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert '"<Enter>"' in text
    assert '"<Leave>"' in text
    assert "unbind_all(" in text
    assert '"<MouseWheel>"' in text


def test_mousewheel_unbinds_on_close():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    close_index = text.index(
        "def _close("
    )

    close_text = text[close_index:]

    assert "unbind_all(" in close_text
    assert '"<MouseWheel>"' in close_text
