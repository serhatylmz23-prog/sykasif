from syk_simulasyon.syk_ui_runtime.adaptive_theme import (
    AdaptiveThemeResolver,
)


def test_gunduz_altin_gece_gumus():
    resolver = AdaptiveThemeResolver()

    assert resolver.resolve(
        hour=12,
        weather="clear",
    ) == "gold"

    assert resolver.resolve(
        hour=23,
        weather="clear",
    ) == "silver"


def test_firtinada_koyu_tema():
    resolver = AdaptiveThemeResolver()

    assert resolver.resolve(
        hour=12,
        weather="storm",
    ) == "dark"


def test_tablet_ve_mobil_tema():
    resolver = AdaptiveThemeResolver()

    assert resolver.resolve(
        hour=12,
        weather="clear",
        device="tablet",
    ) == "tablet"

    assert resolver.resolve(
        hour=12,
        weather="clear",
        device="mobile",
    ) == "mobile"