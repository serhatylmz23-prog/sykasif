from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INDEX = (
    ROOT
    / "terminal_v2"
    / "templates"
    / "index.html"
)

CSS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "css"
    / "canli_modul_gorsel_durum.css"
)

TAG = (
    '<link rel="stylesheet" '
    'href="/static/css/canli_modul_gorsel_durum.css">'
)


def css_source():
    assert CSS.exists()
    return CSS.read_text(encoding="utf-8")


def index_source():
    assert INDEX.exists()
    return INDEX.read_text(encoding="utf-8")


def test_css_var():
    assert CSS.exists()


def test_index_css_tek():
    assert index_source().count(TAG) == 1


def test_css_head_icinde():
    text = index_source()
    assert text.index(TAG) < text.index("</head>")


def test_modul_kodu_selectoru():
    assert "[data-modul-kodu]" in css_source()


def test_aktif_secim_selectoru():
    assert (
        'data-syk-modul-secim="aktif"'
        in css_source()
    )


def test_pasif_secim_selectoru():
    assert (
        'data-syk-modul-secim="pasif"'
        in css_source()
    )


def test_bekliyor_runtime_selectoru():
    assert (
        'data-syk-modul-durum="bekliyor"'
        in css_source()
    )


def test_calisiyor_runtime_selectoru():
    assert (
        'data-syk-modul-durum="calisiyor"'
        in css_source()
    )


def test_durdu_runtime_selectoru():
    assert (
        'data-syk-modul-durum="durdu"'
        in css_source()
    )


def test_cevrimdisi_runtime_selectoru():
    assert (
        'data-syk-modul-durum="cevrimdisi"'
        in css_source()
    )


def test_hareket_selectoru():
    assert (
        'data-syk-modul-hareket="aktif"'
        in css_source()
    )


def test_canli_nabiz_animasyonu():
    assert (
        "@keyframes syk-modul-canli-nabiz"
        in css_source()
    )


def test_reduced_motion_destegi():
    assert (
        "prefers-reduced-motion: reduce"
        in css_source()
    )
