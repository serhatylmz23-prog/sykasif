from pathlib import Path


def test_scroll_position_is_preserved():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "kaydirma_konumu = 0.0" in text
    assert "self.scroll_canvas.yview()" in text
    assert (
        "def _kaydirma_konumunu_geri_yukle("
        in text
    )
    assert "self.scroll_canvas.yview_moveto(" in text


def test_scroll_region_updates_after_cards():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "self.scroll_canvas.update_idletasks()" in text
    assert 'scrollregion=self.scroll_canvas.bbox(' in text
    assert "self.root.after_idle(" in text
