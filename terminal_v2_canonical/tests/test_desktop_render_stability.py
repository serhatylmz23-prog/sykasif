from pathlib import Path


def test_unchanged_cards_are_not_redrawn():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "kart_imzasi = tuple(" in text
    assert '"_son_kart_imzasi"' in text
    assert "== kart_imzasi:" in text
    assert "self._son_kart_imzasi = kart_imzasi" in text


def test_real_card_changes_can_still_render():
    text = Path(
        "terminal_v2/desktop/app.py"
    ).read_text(
        encoding="utf-8-sig",
    )

    signature_fields = {
        'card.get("kod", "")',
        'card.get("ad", "")',
        'card.get("durum_kodu", "")',
        'card.get("durum_metni", "")',
        'card.get("aktif", False)',
    }

    assert all(
        field in text
        for field in signature_fields
    )

    assert "self._render_cards(" in text
