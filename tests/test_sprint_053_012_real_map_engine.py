from pathlib import Path

from terminal_v2_canonical.runtime.map.real_map_engine import (
    GeoPoint,
    LayerState,
    MapLayer,
    MapMode,
    RealMapEngine,
)


LOCK = Path(
    "terminal_v2_canonical/contracts/"
    "KANONIK_UI_SPRINT_053_011.json"
)


def test_canonical_ui_lock_exists():
    assert LOCK.exists()


def test_map_engine_starts_with_real_viewport():
    engine = RealMapEngine()

    assert isinstance(
        engine.viewport.center,
        GeoPoint,
    )

    assert engine.viewport.mode == MapMode.MAP


def test_base_mode_can_change():
    engine = RealMapEngine()

    assert (
        engine.set_mode(MapMode.SATELLITE)
        == MapMode.SATELLITE
    )

    assert (
        engine.set_mode(MapMode.TERRAIN)
        == MapMode.TERRAIN
    )


def test_viewport_can_follow_gps():
    engine = RealMapEngine()

    viewport = engine.set_viewport(
        latitude=38.681,
        longitude=39.226,
        zoom=13.5,
    )

    assert viewport.center.latitude == 38.681
    assert viewport.center.longitude == 39.226
    assert viewport.zoom == 13.5


def test_dynamic_layer_registry_has_no_fixed_limit():
    engine = RealMapEngine()

    for i in range(30):
        engine.register_layer(
            MapLayer(
                id=f"layer-{i}",
                title=f"Katman {i}",
                category="test",
                priority=i,
            )
        )

    assert len(engine.layers) == 30


def test_active_layers_feed_matrix():
    engine = RealMapEngine()

    engine.register_layer(
        MapLayer(
            id="rota",
            title="Rota",
            category="harita",
            priority=10,
        )
    )

    engine.register_layer(
        MapLayer(
            id="iz",
            title="İz",
            category="harita",
            priority=20,
        )
    )

    engine.activate_layer("rota")
    engine.activate_layer("iz")

    payload = engine.matrix_payload()

    assert len(payload) == 2
    assert payload[0]["id"] == "iz"
    assert payload[1]["id"] == "rota"


def test_heavy_layer_is_suspended_when_closed():
    engine = RealMapEngine()

    engine.register_layer(
        MapLayer(
            id="video",
            title="Video",
            category="görüntü",
            heavy=True,
        )
    )

    engine.activate_layer("video")
    layer = engine.deactivate_layer("video")

    assert layer.visible is False
    assert layer.state == LayerState.SUSPENDED


def test_snapshot_contract():
    engine = RealMapEngine()

    result = engine.snapshot()

    assert "viewport" in result
    assert "active_layers" in result
    assert "registered_layer_count" in result
