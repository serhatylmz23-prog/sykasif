from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TERMINAL = ROOT / "terminal_v2"

MAP_HTML = (
    TERMINAL
    / "map"
    / "index.html"
)

REAL_MAP = (
    TERMINAL
    / "static"
    / "js"
    / "harita_real_basemap.js"
)

LAYER_ARCH = (
    TERMINAL
    / "static"
    / "js"
    / "harita_katman_mimarisi.js"
)

TERMINAL_BRIDGE = (
    TERMINAL
    / "static"
    / "js"
    / "harita_terminal_koprusu.js"
)

OLD_CANVAS_JS = (
    TERMINAL
    / "static"
    / "js"
    / "harita_clean_surface.js"
)

OLD_CANVAS_CSS = (
    TERMINAL
    / "static"
    / "css"
    / "harita_clean_surface.css"
)

OLD_RENDERER = (
    TERMINAL
    / "static"
    / "js"
    / "harita_katman_renderer.js"
)


def read(path):
    assert path.exists()
    return path.read_text(
        encoding="utf-8"
    )


def test_single_real_map_engine_exists():
    assert REAL_MAP.exists()
    assert LAYER_ARCH.exists()
    assert TERMINAL_BRIDGE.exists()
    assert MAP_HTML.exists()


def test_obsolete_canvas_engine_removed():
    assert not OLD_CANVAS_JS.exists()
    assert not OLD_CANVAS_CSS.exists()
    assert not OLD_RENDERER.exists()


def test_map_page_uses_real_engine_only():
    html = read(MAP_HTML)

    assert (
        "/static/js/harita_real_basemap.js"
        in html
    )

    assert (
        "/static/js/harita_terminal_koprusu.js"
        in html
    )

    assert (
        "harita_clean_surface.js"
        not in html
    )

    assert (
        "harita_clean_surface.css"
        not in html
    )

    assert (
        "harita_katman_renderer.js"
        not in html
    )


def test_real_basemap_stack():
    js = read(REAL_MAP)

    assert "tile.openstreetmap.org" in js
    assert "World_Imagery" in js
    assert "opentopomap.org" in js
    assert "L.map(" in js
    assert "L.tileLayer(" in js


def test_real_object_layers():
    js = read(REAL_MAP)

    assert "HARITA_NESNELERI" in js
    assert "L.layerGroup()" in js
    assert "createPointLayer" in js
    assert "createLineLayer" in js
    assert "createPolygonLayer" in js
    assert "setObjectLayer" in js


def test_real_layer_architecture():
    js = read(LAYER_ARCH)

    required = (
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

    for token in required:
        assert token in js


def test_terminal_bridge_is_real_map_route():
    js = read(TERMINAL_BRIDGE)

    assert 'MAP_ROUTE =' in js
    assert '"/map"' in js
    assert "SyKasifTerminalMapBridge" in js


def test_obsolete_dom_contract_absent_from_product():
    product_text = ""

    for path in TERMINAL.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".js",
            ".html",
            ".css",
        }:
            continue

        product_text += path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    assert (
        "data-syk-object-layer"
        not in product_text
    )