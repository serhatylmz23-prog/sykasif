from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from threading import RLock
from typing import Any
from uuid import uuid4

from syk_core.goruntu.frame.media_analysis_pipeline import (
    MediaAnalysisPipeline,
)

from .sealed_report import (
    ReportEvidence,
    SealedReportEngine,
    SealedReportRequest,
)


SUPPORTED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
}

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class StoredMediaAnalysis:
    analysis_id: str
    media_id: str
    source_name: str
    source_sha256: str
    source_path: str
    result_path: str
    pdf_path: str
    manifest_path: str
    report_sha256: str
    manifest_sha256: str
    candidate_count: int
    dtse_created_count: int
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "media_id": self.media_id,
            "source_name": self.source_name,
            "source_sha256": self.source_sha256,
            "source_path": self.source_path,
            "result_path": self.result_path,
            "pdf_path": self.pdf_path,
            "manifest_path": self.manifest_path,
            "report_sha256": self.report_sha256,
            "manifest_sha256": (
                self.manifest_sha256
            ),
            "candidate_count": (
                self.candidate_count
            ),
            "dtse_created_count": (
                self.dtse_created_count
            ),
            "created_at": self.created_at,
            "analysis_scope": (
                "digital_media_analysis"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


class DTSEEngineBridge:
    """
    Mevcut DTSE motoruna doğrudan Python içinden bağlanır.
    Motor bulunamazsa sessizce simülasyon üretmez;
    bağlantı durumunu açıkça bildirir.
    """

    def dispatch(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            from . import dtse_attention_routes
            from .dtse_attention_engine import (
                AttentionSignal,
                NormalizedBox,
            )
        except ImportError as error:
            return {
                "connected": False,
                "created_count": 0,
                "reason": (
                    "dtse_import_failed"
                ),
                "detail": str(error),
            }

        engine = self._find_engine(
            dtse_attention_routes
        )

        if engine is None:
            return {
                "connected": False,
                "created_count": 0,
                "reason": (
                    "dtse_engine_not_found"
                ),
            }

        signals = [
            AttentionSignal(
                label=item["label"],
                kind=item.get(
                    "kind",
                    "anomaly",
                ),
                confidence=float(
                    item["confidence"]
                ),
                box=NormalizedBox(
                    x=float(item["box"]["x"]),
                    y=float(item["box"]["y"]),
                    width=float(
                        item["box"]["width"]
                    ),
                    height=float(
                        item["box"]["height"]
                    ),
                ),
                description=item.get(
                    "description",
                    "",
                ),
                metrics=item.get(
                    "metrics",
                    {},
                ),
                evidence_refs=item.get(
                    "evidence_refs",
                    [],
                ),
            )
            for item in payload.get(
                "signals",
                []
            )
        ]

        method = self._find_method(engine)

        if method is None:
            return {
                "connected": False,
                "created_count": 0,
                "reason": (
                    "dtse_ingest_method_not_found"
                ),
            }

        result = method(
            media_id=payload["media_id"],
            source_kind=payload["source_kind"],
            frame_index=payload[
                "frame_index"
            ],
            timestamp_ms=payload[
                "timestamp_ms"
            ],
            frame_width=payload[
                "frame_width"
            ],
            frame_height=payload[
                "frame_height"
            ],
            signals=signals,
        )

        if not isinstance(result, dict):
            return {
                "connected": True,
                "created_count": len(signals),
                "result": result,
            }

        return {
            "connected": True,
            "created_count": int(
                result.get(
                    "created_count",
                    len(
                        result.get(
                            "events",
                            [],
                        )
                    ),
                )
            ),
            "result": result,
        }

    @staticmethod
    def _find_engine(module):
        preferred = (
            "dtse_attention_engine",
            "attention_engine",
            "engine",
        )

        for name in preferred:
            candidate = getattr(
                module,
                name,
                None,
            )

            if candidate is not None:
                return candidate

        for value in vars(
            module
        ).values():
            if any(
                callable(
                    getattr(
                        value,
                        method,
                        None,
                    )
                )
                for method in (
                    "ingest",
                    "ingest_frame",
                    "process_frame",
                )
            ):
                return value

        return None

    @staticmethod
    def _find_method(engine):
        for name in (
            "ingest",
            "ingest_frame",
            "process_frame",
        ):
            method = getattr(
                engine,
                name,
                None,
            )

            if callable(method):
                return method

        return None


class MediaUploadService:
    def __init__(
        self,
        *,
        artifact_root: str | Path | None = None,
        pipeline: MediaAnalysisPipeline | None = None,
        report_engine: SealedReportEngine | None = None,
        dtse_bridge: DTSEEngineBridge | None = None,
    ) -> None:
        configured_root = (
            artifact_root
            or os.getenv(
                "SYK_MEDIA_ARTIFACT_ROOT"
            )
            or "artifacts/media_analysis"
        )

        self.artifact_root = Path(
            configured_root
        )

        self.artifact_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.pipeline = (
            pipeline
            or MediaAnalysisPipeline()
        )

        self.report_engine = (
            report_engine
            or SealedReportEngine()
        )

        self.dtse_bridge = (
            dtse_bridge
            or DTSEEngineBridge()
        )

        self._records: dict[
            str,
            StoredMediaAnalysis,
        ] = {}

        self._lock = RLock()

    def analyze(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
        media_id: str | None = None,
        location: str = "Belirtilmedi",
    ) -> dict[str, Any]:
        self._validate(
            filename=filename,
            content_type=content_type,
            content=content,
        )

        resolved_media_id = (
            self._safe_media_id(media_id)
            if media_id
            else self._new_media_id()
        )

        analysis_id = (
            f"ANL-{uuid4().hex[:24]}"
        )

        analysis_root = (
            self.artifact_root
            / analysis_id
        )

        analysis_root.mkdir(
            parents=True,
            exist_ok=False,
        )

        extension = (
            Path(filename).suffix.lower()
            or self._extension_for(
                content_type
            )
        )

        source_path = (
            analysis_root
            / f"source{extension}"
        )

        source_path.write_bytes(content)

        pipeline_result = (
            self.pipeline.analyze_image(
                media_id=resolved_media_id,
                content=content,
                frame_index=0,
                timestamp_ms=0,
                source_kind="image",
                source_name=filename,
            )
        )

        dtse_result = (
            self.dtse_bridge.dispatch(
                pipeline_result.dtse_payload
            )
        )

        evidence_items = tuple(
            ReportEvidence(
                evidence_id=item[
                    "evidence_id"
                ],
                title=item["title"],
                description=item[
                    "description"
                ],
                confidence=float(
                    item["confidence"]
                ),
                status=item["status"],
                source=item["source"],
                sha256=item["sha256"],
            )
            for item in pipeline_result
            .report_payload[
                "evidences"
            ]
        )

        request = SealedReportRequest(
            session_id=resolved_media_id,
            title=(
                "SyKaşif Görüntü İncelemesi"
            ),
            research_type="Fotoğraf",
            location=location,
            started_at=datetime.now(
                UTC
            ).isoformat(),
            ended_at=datetime.now(
                UTC
            ).isoformat(),
            summary=(
                f"{len(evidence_items)} dijital "
                "dikkat bölgesi adayı üretildi. "
                f"DTSE kayıt sayısı: "
                f"{dtse_result.get('created_count', 0)}."
            ),
            evidences=evidence_items,
            metadata={
                "analysis_id": analysis_id,
                "source_name": filename,
                "source_sha256": sha256(
                    content
                ).hexdigest(),
                "decoded": (
                    pipeline_result
                    .decoded
                    .as_dict()
                ),
                "motion": (
                    pipeline_result
                    .motion
                    .as_dict()
                ),
                "dtse": dtse_result,
            },
        )

        pdf_path = (
            analysis_root
            / "sykasif_raporu.pdf"
        )

        report_result = (
            self.report_engine.render(
                request,
                pdf_path,
            )
        )

        result_payload = {
            "schema": (
                "sykasif-media-upload-result/v1"
            ),
            "analysis_id": analysis_id,
            "media_id": resolved_media_id,
            "source_name": filename,
            "source_sha256": sha256(
                content
            ).hexdigest(),
            "pipeline": (
                pipeline_result.as_dict()
            ),
            "dtse": dtse_result,
            "report": report_result,
            "analysis_scope": (
                "digital_media_analysis"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }

        result_path = (
            analysis_root
            / "analysis.json"
        )

        result_path.write_text(
            json.dumps(
                result_payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )

        record = StoredMediaAnalysis(
            analysis_id=analysis_id,
            media_id=resolved_media_id,
            source_name=filename,
            source_sha256=sha256(
                content
            ).hexdigest(),
            source_path=str(source_path),
            result_path=str(result_path),
            pdf_path=report_result[
                "output_path"
            ],
            manifest_path=report_result[
                "manifest_path"
            ],
            report_sha256=report_result[
                "report_sha256"
            ],
            manifest_sha256=report_result[
                "manifest_sha256"
            ],
            candidate_count=len(
                pipeline_result
                .candidates
                .candidates
            ),
            dtse_created_count=int(
                dtse_result.get(
                    "created_count",
                    0,
                )
            ),
            created_at=datetime.now(
                UTC
            ).isoformat(),
        )

        with self._lock:
            self._records[
                analysis_id
            ] = record

        return {
            **record.as_dict(),
            "dtse_connected": bool(
                dtse_result.get(
                    "connected",
                    False,
                )
            ),
            "download_url": (
                "/api/syk-ui/media-analysis/"
                f"{analysis_id}/report"
            ),
            "manifest_url": (
                "/api/syk-ui/media-analysis/"
                f"{analysis_id}/manifest"
            ),
            "result_url": (
                "/api/syk-ui/media-analysis/"
                f"{analysis_id}"
            ),
        }

    def get(
        self,
        analysis_id: str,
    ) -> StoredMediaAnalysis:
        with self._lock:
            record = self._records.get(
                analysis_id
            )

        if record is None:
            raise KeyError(analysis_id)

        return record

    def read_result(
        self,
        analysis_id: str,
    ) -> dict[str, Any]:
        record = self.get(
            analysis_id
        )

        return json.loads(
            Path(
                record.result_path
            ).read_text(
                encoding="utf-8"
            )
        )

    def list(
        self,
    ) -> list[dict[str, Any]]:
        with self._lock:
            records = list(
                self._records.values()
            )

        return [
            record.as_dict()
            for record in records
        ]

    @staticmethod
    def _validate(
        *,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> None:
        if not filename.strip():
            raise ValueError(
                "Dosya adı boş olamaz."
            )

        if content_type not in (
            SUPPORTED_CONTENT_TYPES
        ):
            raise ValueError(
                "Yalnız JPG, PNG, WebP "
                "ve BMP kabul edilir."
            )

        if not content:
            raise ValueError(
                "Yüklenen dosya boş."
            )

        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError(
                "Dosya 25 MB sınırını aşıyor."
            )

    @staticmethod
    def _new_media_id() -> str:
        return (
            f"MEDIA-{uuid4().hex[:20]}"
        )

    @staticmethod
    def _safe_media_id(
        media_id: str,
    ) -> str:
        value = media_id.strip()

        if not re.fullmatch(
            r"[A-Za-z0-9._-]{3,80}",
            value,
        ):
            raise ValueError(
                "Geçersiz medya kimliği."
            )

        return value

    @staticmethod
    def _extension_for(
        content_type: str,
    ) -> str:
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
        }

        return mapping[content_type]