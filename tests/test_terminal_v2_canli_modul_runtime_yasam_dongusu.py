from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENGINE = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_durum_motoru.js"
)

CSS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "css"
    / "canli_modul_gorsel_durum.css"
)


def engine():
    return ENGINE.read_text(encoding="utf-8")


def css():
    return CSS.read_text(encoding="utf-8")


def test_runtime_durumlari():
    text = engine()
    assert 'CALISIYOR: "calisiyor"' in text
    assert 'BEKLIYOR: "bekliyor"' in text
    assert 'DURDU: "durdu"' in text
    assert 'CEVRIMDISI: "cevrimdisi"' in text


def test_runtime_dom_kaynagi():
    assert "[data-runtime-durum]" in engine()


def test_runtime_normalizer():
    assert "runtimeDurumunuNormalizeEt" in engine()


def test_secim_runtime_ayri():
    text = engine()
    assert "dataset.sykModulSecim" in text
    assert "dataset.sykModulDurum" in text


def test_hareket_sadece_calisiyor():
    text = engine()
    assert (
        "runtimeDurum === DURUMLAR.CALISIYOR"
        in text
    )


def test_css_bekliyor():
    assert (
        'data-syk-modul-durum="bekliyor"'
        in css()
    )


def test_css_calisiyor():
    assert (
        'data-syk-modul-durum="calisiyor"'
        in css()
    )


def test_css_durdu():
    assert (
        'data-syk-modul-durum="durdu"'
        in css()
    )


def test_css_cevrimdisi():
    assert (
        'data-syk-modul-durum="cevrimdisi"'
        in css()
    )


def test_hareket_animasyonu():
    assert (
        'data-syk-modul-hareket="aktif"'
        in css()
    )
