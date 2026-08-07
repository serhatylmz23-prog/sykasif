from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INDEX = ROOT / "terminal_v2" / "templates" / "index.html"

ENGINE = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_durum_motoru.js"
)

BOOT = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_boot.js"
)

TAG = (
    '<script type="module" '
    'src="/static/js/canli_modul_gorsel_boot.js">'
    '</script>'
)


def test_engine_var():
    assert ENGINE.exists()


def test_boot_var():
    assert BOOT.exists()


def test_index_boot_tek():
    text = INDEX.read_text(encoding="utf-8")
    assert text.count(TAG) == 1


def test_boot_engine_import():
    text = BOOT.read_text(encoding="utf-8")
    assert (
        'from "./canli_modul_gorsel_durum_motoru.js"'
        in text
    )


def test_boot_bind_fonksiyonunu_kullanir():
    text = BOOT.read_text(encoding="utf-8")
    assert "bindCanliModulGorselDurumMotoru" in text


def test_boot_idempotent():
    text = BOOT.read_text(encoding="utf-8")
    assert "__SYK_MODULE_VISUAL_BOOT_V1__" in text
    assert "globalThis[SYK_MODULE_VISUAL_BOOT_KEY]" in text


def test_boot_otomatik():
    text = BOOT.read_text(encoding="utf-8")
    assert "bootCanliModulGorselDurumMotoru();" in text


def test_index_body_icinde():
    text = INDEX.read_text(encoding="utf-8")
    assert text.index(TAG) < text.index("</body>")
