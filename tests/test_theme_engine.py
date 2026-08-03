from syk_simulasyon.syk_ui_runtime.theme_engine import (
    ThemeEngine,
)


def test_tema_motoru_temalari_yukler():
    engine = ThemeEngine()

    assert "gold" in engine.registry.ids()
    assert "silver" in engine.registry.ids()
    assert "dark" in engine.registry.ids()


def test_tema_motoru_durum_uretir():
    engine = ThemeEngine()

    snapshot = engine.snapshot()

    assert snapshot[
        "schema"
    ] == "sykasif-theme-engine/v1"

    assert snapshot["runtime"]["active"][
        "id"
    ] == "gold"