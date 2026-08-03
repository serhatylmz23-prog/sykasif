from pathlib import Path

from syk_simulasyon.syk_ui_runtime.sealed_report import (
    ReportEvidence,
    ReportScientificResult,
    SealedReportEngine,
    SealedReportRequest,
)


def _request() -> SealedReportRequest:
    return SealedReportRequest(
        session_id="SESSION-PDF-001",
        title="SyKaşif Görüntü İncelemesi",
        research_type="Fotoğraf",
        location="Dijital test ortamı",
        started_at=(
            "2026-08-03T10:00:00+00:00"
        ),
        ended_at=(
            "2026-08-03T10:10:00+00:00"
        ),
        summary=(
            "DTSE ve bilimsel modül "
            "sonuçlarının rapor testidir."
        ),
        evidences=(
            ReportEvidence(
                evidence_id="EVD-001",
                title="Doku değişimi adayı",
                description=(
                    "Seçili bölgede açıklanabilir "
                    "doku farklılığı belirlenmiştir."
                ),
                confidence=88.4,
                status="candidate",
                source=(
                    "frame_candidate_engine"
                ),
                sha256="a" * 64,
            ),
        ),
        scientific_results=(
            ReportScientificResult(
                module_id="thermal",
                title="Termal Analiz",
                value="24.72 °C",
                confidence=87.0,
                status="preview",
                source="digital_preview",
            ),
        ),
    )


def test_rapor_manifesti_kararli_sha_uretir():
    engine = SealedReportEngine()
    request = _request()

    first = engine.manifest(request)
    second = engine.manifest(request)

    assert (
        first["manifest_sha256"]
        == second["manifest_sha256"]
    )

    assert len(
        first["manifest_sha256"]
    ) == 64

    assert (
        first[
            "maximum_digital_confidence"
        ]
        == 99.9
    )


def test_muhurlu_pdf_ve_manifest_uretilir(
    tmp_path: Path,
):
    engine = SealedReportEngine()

    output = (
        tmp_path
        / "sykasif_test_raporu.pdf"
    )

    result = engine.render(
        _request(),
        output,
    )

    assert output.is_file()
    assert output.stat().st_size > 1500

    assert output.read_bytes().startswith(
        b"%PDF-"
    )

    assert len(
        result["report_sha256"]
    ) == 64

    manifest_path = Path(
        result["manifest_path"]
    )

    assert manifest_path.is_file()

    manifest_text = (
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        "manifest_sha256"
        in manifest_text
    )

    assert (
        "report_sha256"
        in manifest_text
    )

    assert (
        "digital_analysis_only"
        in manifest_text
    )


def test_rapor_saha_dogrulamasi_uyarisi_tasir():
    engine = SealedReportEngine()

    manifest = engine.manifest(
        _request()
    )

    assert manifest[
        "field_validation_required"
    ]

    assert (
        manifest["analysis_scope"]
        == "digital_analysis_only"
    )