from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

HTML = (
    ROOT
    / "terminal_v2"
    / "map"
    / "index.html"
)

MAP_JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "harita_real_basemap.js"
)

BRIDGE_JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "harita_terminal_koprusu.js"
)


def read(path):
    assert path.exists()

    return path.read_text(
        encoding="utf-8"
    )


def test_terminal_map_bridge_exists():
    assert BRIDGE_JS.exists()


def test_bridge_contract():
    text = read(BRIDGE_JS)

    required = [
        "SYK_TERMINAL_MAP_BRIDGE_V1",
        "MAP_MODULE_CODE",
        "MAP_ROUTE",
        "sykasif:aktif-modul-guncellendi",
        "openMap",
        "openMapNewWindow",
        "isMapModule",
        "handleRuntimeModuleEvent",
        "SyKasifTerminalMapBridge",
    ]

    for token in required:
        assert token in text


def test_map_page_loads_bridge():
    html = read(HTML)

    assert (
        "/static/js/harita_terminal_koprusu.js"
        in html
    )


def test_real_basemap_preserved():
    text = read(MAP_JS)

    assert "tile.openstreetmap.org" in text
    assert "World_Imagery" in text
    assert "opentopomap.org" in text


def test_real_layers_preserved():
    text = read(MAP_JS)

    assert "HARITA_NESNELERI" in text
    assert "setObjectLayer" in text


def test_map_route_is_real_route():
    text = read(BRIDGE_JS)

    assert '"/map"' in text


def test_no_old_terminal_runtime_dependency():
    text = read(BRIDGE_JS)

    for forbidden in (
        "terminal_routes",
        "runtime_fastapi_sunucusu",
        "syk_ui_runtime",
    ):
        assert forbidden not in text
