from pathlib import Path


def test_desktop_has_vertical_scroll():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "self.scroll_canvas = tk.Canvas(" in text
    assert "self.scrollbar = ttk.Scrollbar(" in text
    assert 'orient="vertical"' in text
    assert "scrollregion=self.scroll_canvas.bbox" in text
    assert 'bind_all(\n            "<MouseWheel>"' in text
    assert "def _on_mousewheel(" in text


def test_scroll_canvas_fills_window():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert 'side="left"' in text
    assert 'fill="both"' in text
    assert "expand=True" in text
    assert "width=event.width" in text
