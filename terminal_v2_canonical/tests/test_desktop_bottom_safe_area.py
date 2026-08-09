from pathlib import Path


def uygulama_kaynagi() -> str:
    return Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )


def test_bottom_safe_area_exists():
    text = uygulama_kaynagi()

    assert (
        "self.bottom_safe_area = tk.Frame("
        in text
    )
    assert "height=120" in text
    assert "self.bottom_safe_area.pack(" in text


def test_bottom_safe_area_keeps_height():
    text = uygulama_kaynagi()

    assert (
        "self.bottom_safe_area.pack_propagate("
        in text
    )
    assert "False" in text
