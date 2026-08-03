from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


REPORT_SCHEMA = "sykasif-sealed-report/v1"
MAXIMUM_DIGITAL_CONFIDENCE = 99.9


@dataclass(frozen=True, slots=True)
class ReportEvidence:
    evidence_id: str
    title: str
    description: str
    confidence: float
    status: str
    source: str
    sha256: str
    field_validation_required: bool = True


@dataclass(frozen=True, slots=True)
class ReportScientificResult:
    module_id: str
    title: str
    value: str
    confidence: float
    status: str
    source: str


@dataclass(frozen=True, slots=True)
class SealedReportRequest:
    session_id: str
    title: str
    research_type: str
    location: str = "Belirtilmedi"
    started_at: str = ""
    ended_at: str = ""
    summary: str = ""
    evidences: tuple[ReportEvidence, ...] = ()
    scientific_results: tuple[
        ReportScientificResult,
        ...,
    ] = ()
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class SealedReportEngine:
    def __init__(self) -> None:
        self.font_regular = "Helvetica"
        self.font_bold = "Helvetica-Bold"
        self._register_font()

    def _register_font(self) -> None:
        candidates = (
            (
                Path("C:/Windows/Fonts/arial.ttf"),
                Path("C:/Windows/Fonts/arialbd.ttf"),
            ),
            (
                Path(
                    "/usr/share/fonts/truetype/"
                    "dejavu/DejaVuSans.ttf"
                ),
                Path(
                    "/usr/share/fonts/truetype/"
                    "dejavu/DejaVuSans-Bold.ttf"
                ),
            ),
        )

        for regular, bold in candidates:
            if not regular.is_file():
                continue

            if not bold.is_file():
                continue

            pdfmetrics.registerFont(
                TTFont(
                    "SyKasifRegular",
                    str(regular),
                )
            )

            pdfmetrics.registerFont(
                TTFont(
                    "SyKasifBold",
                    str(bold),
                )
            )

            self.font_regular = (
                "SyKasifRegular"
            )

            self.font_bold = (
                "SyKasifBold"
            )

            return

    @staticmethod
    def _canonical_bytes(
        payload: dict[str, Any],
    ) -> bytes:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def manifest(
        self,
        request: SealedReportRequest,
    ) -> dict[str, Any]:
        unsigned = {
            "schema": REPORT_SCHEMA,
            "session_id": request.session_id,
            "title": request.title,
            "research_type": (
                request.research_type
            ),
            "location": request.location,
            "started_at": request.started_at,
            "ended_at": request.ended_at,
            "summary": request.summary,
            "evidences": [
                asdict(item)
                for item in request.evidences
            ],
            "scientific_results": [
                asdict(item)
                for item
                in request.scientific_results
            ],
            "metadata": request.metadata,
            "evidence_count": len(
                request.evidences
            ),
            "scientific_result_count": len(
                request.scientific_results
            ),
            "analysis_scope": (
                "digital_analysis_only"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": (
                MAXIMUM_DIGITAL_CONFIDENCE
            ),
        }

        manifest_sha256 = sha256(
            self._canonical_bytes(unsigned)
        ).hexdigest()

        return {
            **unsigned,
            "manifest_sha256": (
                manifest_sha256
            ),
        }

    def render(
        self,
        request: SealedReportRequest,
        output_path: str | Path,
    ) -> dict[str, Any]:
        output = Path(output_path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        manifest = self.manifest(
            request
        )

        styles = self._styles()

        document = BaseDocTemplate(
            str(output),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=20 * mm,
            title=request.title,
            author="SyKaşif",
            subject=(
                "Mühürlü dijital analiz raporu"
            ),
        )

        frame = Frame(
            document.leftMargin,
            document.bottomMargin,
            document.width,
            document.height,
            id="main",
        )

        template = PageTemplate(
            id="sealed-report",
            frames=[frame],
            onPage=self._draw_page,
        )

        document.addPageTemplates(
            [template]
        )

        story = []

        story.extend(
            self._cover(
                request=request,
                manifest=manifest,
                styles=styles,
            )
        )

        story.append(PageBreak())

        story.extend(
            self._summary(
                request=request,
                manifest=manifest,
                styles=styles,
            )
        )

        if request.evidences:
            story.append(PageBreak())

            story.extend(
                self._evidence_pages(
                    request.evidences,
                    styles,
                )
            )

        if request.scientific_results:
            story.append(PageBreak())

            story.extend(
                self._scientific_page(
                    request.scientific_results,
                    styles,
                )
            )

        story.append(PageBreak())

        story.extend(
            self._verification_page(
                manifest,
                styles,
            )
        )

        document.build(story)

        report_sha256 = sha256(
            output.read_bytes()
        ).hexdigest()

        manifest_path = output.with_suffix(
            ".manifest.json"
        )

        manifest_path.write_text(
            json.dumps(
                {
                    **manifest,
                    "report_sha256": (
                        report_sha256
                    ),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        return {
            "schema": REPORT_SCHEMA,
            "session_id": request.session_id,
            "output_path": str(output),
            "manifest_path": str(
                manifest_path
            ),
            "manifest_sha256": manifest[
                "manifest_sha256"
            ],
            "report_sha256": (
                report_sha256
            ),
            "report_size": (
                output.stat().st_size
            ),
            "generated_at": datetime.now(
                UTC
            ).isoformat(),
            "field_validation_required": True,
            "maximum_digital_confidence": (
                MAXIMUM_DIGITAL_CONFIDENCE
            ),
        }

    def _styles(
        self,
    ) -> dict[str, ParagraphStyle]:
        return {
            "title": ParagraphStyle(
                "sykasif-title",
                fontName=self.font_bold,
                fontSize=25,
                leading=30,
                alignment=TA_CENTER,
                textColor="#17313A",
                spaceAfter=8 * mm,
            ),
            "subtitle": ParagraphStyle(
                "sykasif-subtitle",
                fontName=self.font_regular,
                fontSize=11,
                leading=16,
                alignment=TA_CENTER,
                textColor="#49666F",
                spaceAfter=6 * mm,
            ),
            "heading": ParagraphStyle(
                "sykasif-heading",
                fontName=self.font_bold,
                fontSize=14,
                leading=19,
                textColor="#17313A",
                spaceBefore=3 * mm,
                spaceAfter=4 * mm,
            ),
            "body": ParagraphStyle(
                "sykasif-body",
                fontName=self.font_regular,
                fontSize=9.5,
                leading=14,
                textColor="#263D44",
                spaceAfter=3 * mm,
            ),
            "small": ParagraphStyle(
                "sykasif-small",
                fontName=self.font_regular,
                fontSize=7.5,
                leading=11,
                textColor="#58727A",
            ),
            "warning": ParagraphStyle(
                "sykasif-warning",
                fontName=self.font_bold,
                fontSize=10.5,
                leading=16,
                alignment=TA_CENTER,
                textColor="#8C2D22",
                borderColor="#8C2D22",
                borderWidth=0.7,
                borderPadding=9,
                spaceBefore=6 * mm,
                spaceAfter=5 * mm,
            ),
        }

    def _cover(
        self,
        *,
        request: SealedReportRequest,
        manifest: dict[str, Any],
        styles: dict[str, ParagraphStyle],
    ) -> list:
        return [
            Spacer(1, 28 * mm),
            Paragraph(
                "SyKaşif",
                styles["title"],
            ),
            Paragraph(
                "MÜHÜRLÜ DİJİTAL RAPOR",
                styles["subtitle"],
            ),
            Spacer(1, 10 * mm),
            Paragraph(
                escape(request.title),
                styles["heading"],
            ),
            self._info_table(
                [
                    (
                        "Oturum",
                        request.session_id,
                    ),
                    (
                        "Araştırma türü",
                        request.research_type,
                    ),
                    (
                        "Konum",
                        request.location,
                    ),
                    (
                        "Başlangıç",
                        request.started_at
                        or "Belirtilmedi",
                    ),
                    (
                        "Bitiş",
                        request.ended_at
                        or "Belirtilmedi",
                    ),
                    (
                        "Manifest SHA-256",
                        manifest[
                            "manifest_sha256"
                        ],
                    ),
                ],
                styles,
            ),
            Spacer(1, 10 * mm),
            Paragraph(
                (
                    "Bu rapor yalnızca dijital "
                    "analiz sonuçlarını içerir. "
                    "Saha doğrulaması yapılmadan "
                    "kesin hüküm oluşturmaz."
                ),
                styles["warning"],
            ),
        ]

    def _summary(
        self,
        *,
        request: SealedReportRequest,
        manifest: dict[str, Any],
        styles: dict[str, ParagraphStyle],
    ) -> list:
        return [
            Paragraph(
                "Araştırma Özeti",
                styles["heading"],
            ),
            Paragraph(
                escape(
                    request.summary
                    or "Özet bilgisi girilmedi."
                ),
                styles["body"],
            ),
            self._info_table(
                [
                    (
                        "Kanıt kaydı",
                        str(
                            manifest[
                                "evidence_count"
                            ]
                        ),
                    ),
                    (
                        "Bilimsel sonuç",
                        str(
                            manifest[
                                "scientific_result_count"
                            ]
                        ),
                    ),
                    (
                        "Dijital doğrulama üst sınırı",
                        "%99.9",
                    ),
                    (
                        "Saha doğrulaması",
                        "Zorunlu",
                    ),
                ],
                styles,
            ),
        ]

    def _evidence_pages(
        self,
        evidences: tuple[
            ReportEvidence,
            ...,
        ],
        styles: dict[str, ParagraphStyle],
    ) -> list:
        story = [
            Paragraph(
                "DTSE ve Kanıt Kayıtları",
                styles["heading"],
            )
        ]

        for index, evidence in enumerate(
            evidences,
            start=1,
        ):
            story.extend(
                [
                    Paragraph(
                        (
                            f"{index}. "
                            f"{escape(evidence.title)}"
                        ),
                        styles["heading"],
                    ),
                    Paragraph(
                        escape(
                            evidence.description
                        ),
                        styles["body"],
                    ),
                    self._info_table(
                        [
                            (
                                "Kanıt kimliği",
                                evidence.evidence_id,
                            ),
                            (
                                "Dijital güven",
                                (
                                    f"%"
                                    f"{evidence.confidence:.1f}"
                                ),
                            ),
                            (
                                "Durum",
                                evidence.status,
                            ),
                            (
                                "Kaynak",
                                evidence.source,
                            ),
                            (
                                "SHA-256",
                                evidence.sha256,
                            ),
                        ],
                        styles,
                    ),
                    Spacer(1, 5 * mm),
                ]
            )

        return story

    def _scientific_page(
        self,
        results: tuple[
            ReportScientificResult,
            ...,
        ],
        styles: dict[str, ParagraphStyle],
    ) -> list:
        rows = [
            [
                "Modül",
                "Değer",
                "Güven",
                "Durum",
                "Kaynak",
            ]
        ]

        for result in results:
            rows.append(
                [
                    result.title,
                    result.value,
                    f"%{result.confidence:.1f}",
                    result.status,
                    result.source,
                ]
            )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                37 * mm,
                29 * mm,
                19 * mm,
                30 * mm,
                53 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        self.font_bold,
                    ),
                    (
                        "FONTNAME",
                        (0, 1),
                        (-1, -1),
                        self.font_regular,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        "#DDECEF",
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, -1),
                        "#17313A",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        "#8FAAB1",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        return [
            Paragraph(
                "Bilimsel Modül Sonuçları",
                styles["heading"],
            ),
            table,
        ]

    def _verification_page(
        self,
        manifest: dict[str, Any],
        styles: dict[str, ParagraphStyle],
    ) -> list:
        return [
            Paragraph(
                "Doğrulama ve Manifest",
                styles["heading"],
            ),
            self._info_table(
                [
                    (
                        "Şema",
                        manifest["schema"],
                    ),
                    (
                        "Oturum",
                        manifest["session_id"],
                    ),
                    (
                        "Manifest SHA-256",
                        manifest[
                            "manifest_sha256"
                        ],
                    ),
                    (
                        "Analiz kapsamı",
                        manifest[
                            "analysis_scope"
                        ],
                    ),
                    (
                        "Maksimum dijital güven",
                        "%99.9",
                    ),
                    (
                        "Saha doğrulaması",
                        "Gereklidir",
                    ),
                ],
                styles,
            ),
            Paragraph(
                (
                    "Dijital doğrulama yalnızca "
                    "doğrulanmış koşullar altında "
                    "%99.9 seviyesine kadar hedeflenir. "
                    "%100 kesinlik iddiası bulunmaz."
                ),
                styles["warning"],
            ),
        ]

    def _info_table(
        self,
        rows: list[tuple[str, str]],
        styles: dict[str, ParagraphStyle],
    ) -> Table:
        data = [
            [
                Paragraph(
                    escape(str(label)),
                    styles["small"],
                ),
                Paragraph(
                    escape(str(value)),
                    styles["small"],
                ),
            ]
            for label, value in rows
        ]

        table = Table(
            data,
            colWidths=[
                43 * mm,
                125 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        "#E7F0F2",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        "#9BB0B5",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        return table

    def _draw_page(
        self,
        canvas,
        document,
    ) -> None:
        canvas.saveState()

        canvas.setStrokeColor(
            "#78949B"
        )

        canvas.setLineWidth(0.45)

        canvas.line(
            18 * mm,
            14 * mm,
            192 * mm,
            14 * mm,
        )

        canvas.setFont(
            self.font_regular,
            7,
        )

        canvas.setFillColor(
            "#587078"
        )

        canvas.drawString(
            18 * mm,
            9 * mm,
            (
                "SyKaşif - "
                "Mühürlü Dijital Rapor"
            ),
        )

        canvas.drawRightString(
            192 * mm,
            9 * mm,
            f"Sayfa {document.page}",
        )

        canvas.setStrokeColor(
            "#8C2D22"
        )

        canvas.setFillColor(
            "#8C2D22"
        )

        canvas.circle(
            183 * mm,
            23 * mm,
            7 * mm,
            stroke=1,
            fill=0,
        )

        canvas.setFont(
            self.font_bold,
            5.5,
        )

        canvas.drawCentredString(
            183 * mm,
            22 * mm,
            "DİJİTAL",
        )

        canvas.drawCentredString(
            183 * mm,
            19.5 * mm,
            "MÜHÜR",
        )

        canvas.restoreState()