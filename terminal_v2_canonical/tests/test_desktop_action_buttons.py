from pathlib import Path


def uygulama_kaynagi() -> str:
    return Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )


def test_module_action_frame_exists():
    text = uygulama_kaynagi()

    assert "self.module_action_frame = tk.Frame(" in text
    assert "def _render_module_actions(" in text


def test_module_actions_are_clickable():
    text = uygulama_kaynagi()

    assert "button = tk.Button(" in text
    assert 'cursor="hand2"' in text
    assert "command=lambda secilen=islem:" in text


def test_selected_action_updates_turkish_status():
    text = uygulama_kaynagi()

    assert "def _module_action_selected(" in text
    assert (
        r'mesaj = "\u0130\u015flem '
        r'se\u00e7ildi: "'
        in text
    )
    assert "mesaj + islem" in text


def test_module_actions_refresh_with_active_module():
    text = uygulama_kaynagi()

    assert "self._render_module_actions(" in text
    assert "gorunum.islemler" in text
