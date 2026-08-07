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


def read(path):
    assert path.exists()
    return path.read_text(
        encoding="utf-8"
    )


def test_real_object_panel_exists():
    html = read(HTML)

    assert 'id="syk-object-panel"' in html
    assert 'id="syk-object-title"' in html
    assert 'id="syk-object-content"' in html
    assert 'id="syk-object-close"' in html


def test_old_object_inspector_removed():
    html = read(HTML)

    assert 'id="syk-map-object-inspector"' not in html
    assert 'id="syk-inspector-title"' not in html
    assert 'id="syk-inspector-body"' not in html


def test_object_panel_runtime():
    js = read(JS)

    assert "showObject" in js
    assert "closeObject" in js
    assert 'panel.dataset.open =' in js


def test_point_object_click():
    js = read(JS)

    assert "createPointLayer" in js
    assert 'marker.on(' in js
    assert '"click"' in js
    assert "showObject(" in js


def test_line_object_click():
    js = read(JS)

    assert "createLineLayer" in js
    assert "polyline.on(" in js


def test_polygon_object_click():
    js = read(JS)

    assert "createPolygonLayer" in js
    assert "polygon.on(" in js


def test_object_metadata():
    js = read(JS)

    assert '"ID"' in js
    assert '"Katman"' in js
    assert '"Geometri"' in js
    assert '"Enlem"' in js
    assert '"Boylam"' in js


def test_layer_objects_are_real_geo_objects():
    js = read(JS)

    assert "HARITA_NESNELERI" in js
    assert "object.geometri.coordinates" in js


def test_close_button_connected():
    js = read(JS)

    assert '"syk-object-close"' in js
    assert "closeObject" in js