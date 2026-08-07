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

CSS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "css"
    / "harita_real_basemap.css"
)


def read(path):
    assert path.exists()
    return path.read_text(
        encoding="utf-8"
    )


def test_leaflet_real_surface():
    html = read(HTML)

    assert (
        "leaflet@1.9.4"
        in html
    )

    assert (
        'id="syk-real-map"'
        in html
    )


def test_real_street_basemap():
    js = read(JS)

    assert (
        "tile.openstreetmap.org"
        in js
    )


def test_real_satellite_basemap():
    js = read(JS)

    assert (
        "World_Imagery"
        in js
    )

    assert (
        'satellite'
        in js
    )


def test_real_terrain_basemap():
    js = read(JS)

    assert (
        "opentopomap.org"
        in js
    )

    assert (
        'terrain'
        in js
    )


def test_three_basemap_buttons():
    html = read(HTML)

    assert (
        'data-syk-basemap="street"'
        in html
    )

    assert (
        'data-syk-basemap="satellite"'
        in html
    )

    assert (
        'data-syk-basemap="terrain"'
        in html
    )


def test_real_geo_objects_preserved():
    js = read(JS)

    assert (
        "HARITA_NESNELERI"
        in js
    )

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


def test_visible_layer_control_preserved():
    html = read(HTML)
    js = read(JS)

    assert (
        "[data-syk-layer]"
        in js
    )

    assert (
        'data-syk-layer="kanit"'
        in html
    )

    assert (
        'data-syk-layer="fotograf"'
        in html
    )


def test_object_inspector_preserved():
    html = read(HTML)
    js = read(JS)

    assert (
        'id="syk-object-panel"'
        in html
    )

    assert (
        "showObject"
        in js
    )


def test_live_coordinates():
    js = read(JS)

    assert (
        '"mousemove"'
        in js
    )

    assert (
        "updateCoordinate"
        in js
    )


def test_css_real_map():
    css = read(CSS)

    assert (
        "#syk-real-map"
        in css
    )

    assert (
        ".leaflet-container"
        in css
    )
