from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

HTML = (
    ROOT
    / "terminal_v2"
    / "map"
    / "index.html"
)

JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "harita_real_basemap.js"
)


LAYERS = (
    "arastirma_noktasi",
    "fotograf",
    "video",
    "ses",
    "olcum",
    "rota",
    "iz",
    "kamp",
    "kazi",
    "numune",
    "risk",
    "kanit",
)


def read(path):
    assert path.exists()

    return path.read_text(
        encoding="utf-8"
    )


def test_real_layer_contract_only():
    html = read(HTML)

    for layer in LAYERS:
        assert (
            f'data-syk-layer="{layer}"'
            in html
        )


def test_obsolete_layer_contract_removed():
    html = read(HTML)

    assert (
        "data-syk-object-layer"
        not in html
    )


def test_real_layer_control_runtime():
    js = read(JS)

    assert (
        '[data-syk-layer]'
        in js
    )

    assert (
        "setObjectLayer"
        in js
    )

    assert (
        "activeLayers"
        in js
    )


def test_layer_groups_are_real_map_layers():
    js = read(JS)

    assert (
        "layerGroups"
        in js
    )

    assert (
        "L.layerGroup()"
        in js
    )

    assert (
        "group.addTo("
        in js
    )

    assert (
        "map.removeLayer("
        in js
    )


def test_all_real_geometry_types_supported():
    js = read(JS)

    assert (
        "createPointLayer"
        in js
    )

    assert (
        "createLineLayer"
        in js
    )

    assert (
        "createPolygonLayer"
        in js
    )


def test_real_map_layer_toggle():
    js = read(JS)

    assert (
        "input.checked"
        in js
    )

    assert (
        "setObjectLayer("
        in js
    )


def test_old_canvas_layer_state_removed():
    js = read(JS)

    assert (
        "state.objectLayers"
        not in js
    )

    assert (
        "bindObjectLayerControls"
        not in js
    )