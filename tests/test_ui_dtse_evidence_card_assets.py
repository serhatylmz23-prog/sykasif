from pathlib import Path


STATIC_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
)


def test_dtse_kanit_karti_varliklari():
    javascript = (
        STATIC_ROOT
        / "js"
        / "dtse_evidence_card.js"
    )

    stylesheet = (
        STATIC_ROOT
        / "css"
        / "dtse_evidence_card.css"
    )

    index = STATIC_ROOT / "index.html"

    assert javascript.is_file()
    assert stylesheet.is_file()
    assert index.is_file()

    js_text = javascript.read_text(
        encoding="utf-8"
    )

    css_text = stylesheet.read_text(
        encoding="utf-8"
    )

    index_text = index.read_text(
        encoding="utf-8"
    )

    assert "SyKDTSEEvidenceCard" in js_text
    assert "kanit-zinciri" in js_text
    assert "kanit-manifesti" in js_text
    assert "kanit-dogrula" in js_text
    assert "/api/syk-ui/dtse/live" in js_text

    assert "dtse-evidence-card" in css_text
    assert "dtse-evidence-hashes" in css_text
    assert "rare_anomaly" in css_text

    assert (
        "dtse_evidence_card.css"
        in index_text
    )

    assert (
        "dtse_evidence_card.js"
        in index_text
    )