from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INDEX = (
    ROOT
    / "terminal_v2"
    / "templates"
    / "index.html"
)

BOOT = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_terminal_boot.js"
)

LIFECYCLE = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_terminal_yasam_dongusu.js"
)

MODULE_TAG = (
    '<script type="module" '
    'src="/static/js/rota_iz_terminal_boot.js">'
    '</script>'
)


def index_source():
    assert INDEX.exists()
    return INDEX.read_text(encoding="utf-8")


def boot_source():
    assert BOOT.exists()
    return BOOT.read_text(encoding="utf-8")


def test_boot_module_var():
    assert BOOT.exists()


def test_lifecycle_var():
    assert LIFECYCLE.exists()


def test_index_module_girisi_tek():
    text = index_source()
    assert text.count(MODULE_TAG) == 1


def test_module_girisi_body_icinde():
    text = index_source()
    assert text.index(MODULE_TAG) < text.index("</body>")


def test_boot_lifecycle_import_ediyor():
    text = boot_source()
    assert "bindTerminalRouteTraceLifecycle" in text
    assert (
        'from "./rota_iz_terminal_yasam_dongusu.js"'
        in text
    )


def test_boot_otomatik_calisiyor():
    text = boot_source()
    assert "boot();" in text


def test_boot_cift_baslatmayi_engelliyor():
    text = boot_source()
    assert "__SYK_ROUTE_TRACE_BOOT_V1__" in text
    assert "globalThis[SYK_ROUTE_TRACE_BOOT_KEY]" in text


def test_aktif_hareketli_baslangic():
    text = boot_source()
    assert 'state: "aktif"' in text
    assert "motion: true" in text


def test_static_url_dogru():
    text = index_source()
    assert (
        "/static/js/rota_iz_terminal_boot.js"
        in text
    )
