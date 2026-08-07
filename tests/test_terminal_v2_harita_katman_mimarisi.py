from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

LAYER_JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "harita_katman_mimarisi.js"
)


def source():
    assert LAYER_JS.exists()

    return LAYER_JS.read_text(
        encoding="utf-8"
    )


def test_layer_architecture_exists():
    assert LAYER_JS.exists()


def test_layer_version():
    text = source()

    assert (
        "SYK_MAP_LAYER_ARCH_V1"
        in text
    )


def test_required_layer_types():
    text = source()

    required = [
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
    ]

    for token in required:
        assert token in text


def test_geo_geometry_types():
    text = source()

    assert '"Point"' in text
    assert '"LineString"' in text
    assert '"Polygon"' in text


def test_layer_registry():
    text = source()

    assert (
        "HARITA_KATMANLARI"
        in text
    )

    assert (
        "HARITA_KATMAN_TURLERI"
        in text
    )


def test_map_objects():
    text = source()

    assert (
        "HARITA_NESNELERI"
        in text
    )

    assert (
        "ARASTIRMA-001"
        in text
    )

    assert (
        "ROTA-001"
        in text
    )

    assert (
        "KANIT-001"
        in text
    )


def test_layer_lookup_api():
    text = source()

    assert (
        "katmanGetir"
        in text
    )

    assert (
        "katmanNesneleri"
        in text
    )

    assert (
        "aktifKatmanKodlari"
        in text
    )

    assert (
        "katmanOzeti"
        in text
    )


def test_global_contract():
    text = source()

    assert (
        "SyKasifHaritaKatmanlari"
        in text
    )


def test_evidence_sha_contract():
    text = source()

    assert "sha256" in text


def test_no_old_runtime_dependency():
    text = source()

    assert (
        "terminal_routes"
        not in text
    )

    assert (
        "runtime_fastapi_sunucusu"
        not in text
    )

    assert (
        "syk_ui_runtime"
        not in text
    )
