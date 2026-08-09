from pathlib import Path


def uygulama_kaynagi() -> str:
    return Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )


def test_desktop_has_vertical_scroll():
    text = uygulama_kaynagi()

    assert "self.scroll_canvas = tk.Canvas(" in text
    assert "self.scrollbar = ttk.Scrollbar(" in text
    assert 'orient="vertical"' in text
    assert "command=self.scroll_canvas.yview" in text
    assert "yscrollcommand=self.scrollbar.set" in text
    assert "scrollregion=self.scroll_canvas.bbox" in text
    assert "def _on_mousewheel(" in text


def test_mousewheel_binding_is_scoped():
    text = uygulama_kaynagi()

    assert '"<Enter>"' in text
    assert '"<Leave>"' in text
    assert "self.scroll_canvas.bind_all(" in text
    assert "self.scroll_canvas.unbind_all(" in text
    assert '"<MouseWheel>"' in text


def test_scroll_canvas_fills_window():
    text = uygulama_kaynagi()

    assert 'side="left"' in text
    assert 'fill="both"' in text
    assert "expand=True" in text
    assert "width=event.width" in text


def test_scroll_position_is_preserved():
    text = uygulama_kaynagi()

    assert "kaydirma_konumu = 0.0" in text
    assert "self.scroll_canvas.yview()" in text
    assert (
        "def _kaydirma_konumunu_geri_yukle("
        in text
    )
    assert "self.scroll_canvas.yview_moveto(" in text
