from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import math
from threading import RLock
from typing import Any, Callable

from PIL import Image, UnidentifiedImageError

from .candidate_engine import (
    CandidateAnalysis,
    FrameCandidate,
    FrameCandidateEngine,
)
from .frame_ingestion import (
    FrameIngestionEngine,
)
from .frame_models import (
    FrameIngestionResult,
    FramePacket,
    FrameRecord,
)


SUPPORTED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
    "BMP",
}


@dataclass(frozen=True, slots=True)
class DecodedFrame:
    width: int
    height: int
    channels: int
    pixels: bytes
    image_format: str
    source_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "image_format": self.image_format,
            "source_sha256": (
                self.source_sha256
            ),
            "pixel_size": len(self.pixels),
        }


@dataclass(frozen=True, slots=True)
class MotionResult:
    available: bool
    changed_ratio: float
    mean_delta: float
    maximum_delta: float
    motion_detected: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "changed_ratio": round(
                self.changed_ratio,
                6,
            ),
            "mean_delta": round(
                self.mean_delta,
                6,
            ),
            "maximum_delta": round(
                self.maximum_delta,
                6,
            ),
            "motion_detected": (
                self.motion_detected
            ),
        }


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    media_id: str
    frame_id: str
    frame_index: int
    timestamp_ms: int
    source_kind: str
    frame_sha256: str
    candidate_count: int
    motion_detected: bool
    changed_ratio: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "media_id": self.media_id,
            "frame_id": self.frame_id,
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "source_kind": self.source_kind,
            "frame_sha256": (
                self.frame_sha256
            ),
            "candidate_count": (
                self.candidate_count
            ),
            "motion_detected": (
                self.motion_detected
            ),
            "changed_ratio": round(
                self.changed_ratio,
                6,
            ),
        }


@dataclass(frozen=True, slots=True)
class MediaAnalysisResult:
    ingestion: FrameIngestionResult
    decoded: DecodedFrame
    candidates: CandidateAnalysis
    motion: MotionResult
    timeline_entry: TimelineEntry
    dtse_payload: dict[str, Any]
    report_payload: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-media-analysis/v1"
            ),
            "ingestion": (
                self.ingestion.as_dict()
            ),
            "decoded": self.decoded.as_dict(),
            "candidates": (
                self.candidates.as_dict()
            ),
            "motion": self.motion.as_dict(),
            "timeline_entry": (
                self.timeline_entry.as_dict()
            ),
            "dtse_payload": self.dtse_payload,
            "report_payload": (
                self.report_payload
            ),
            "analysis_scope": (
                "digital_media_candidates"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


class ImageDecoder:
    def decode(
        self,
        content: bytes,
    ) -> DecodedFrame:
        if not isinstance(content, bytes):
            raise TypeError(
                "Görüntü içeriği bytes olmalıdır."
            )

        if not content:
            raise ValueError(
                "Görüntü içeriği boş olamaz."
            )

        source_sha256 = sha256(
            content
        ).hexdigest()

        try:
            with Image.open(
                BytesIO(content)
            ) as image:
                image_format = (
                    image.format or "UNKNOWN"
                ).upper()

                if (
                    image_format
                    not in SUPPORTED_IMAGE_FORMATS
                ):
                    raise ValueError(
                        "Desteklenmeyen görüntü "
                        f"biçimi: {image_format}"
                    )

                normalized = image.convert("RGB")
                normalized.load()

                return DecodedFrame(
                    width=normalized.width,
                    height=normalized.height,
                    channels=3,
                    pixels=normalized.tobytes(),
                    image_format=image_format,
                    source_sha256=(
                        source_sha256
                    ),
                )

        except UnidentifiedImageError as error:
            raise ValueError(
                "Görüntü dosyası çözülemedi."
            ) from error


class MotionDetector:
    def __init__(
        self,
        *,
        pixel_threshold: float = 0.10,
        ratio_threshold: float = 0.03,
    ) -> None:
        if not 0.0 <= pixel_threshold <= 1.0:
            raise ValueError(
                "Piksel hareket eşiği "
                "0 ile 1 arasında olmalıdır."
            )

        if not 0.0 <= ratio_threshold <= 1.0:
            raise ValueError(
                "Hareket oranı eşiği "
                "0 ile 1 arasında olmalıdır."
            )

        self.pixel_threshold = (
            pixel_threshold
        )

        self.ratio_threshold = (
            ratio_threshold
        )

    def compare(
        self,
        previous: bytes | None,
        current: bytes,
    ) -> MotionResult:
        if previous is None:
            return MotionResult(
                available=False,
                changed_ratio=0.0,
                mean_delta=0.0,
                maximum_delta=0.0,
                motion_detected=False,
            )

        if len(previous) != len(current):
            return MotionResult(
                available=False,
                changed_ratio=0.0,
                mean_delta=0.0,
                maximum_delta=0.0,
                motion_detected=False,
            )

        if not current:
            return MotionResult(
                available=False,
                changed_ratio=0.0,
                mean_delta=0.0,
                maximum_delta=0.0,
                motion_detected=False,
            )

        changed = 0
        delta_total = 0.0
        maximum_delta = 0.0

        for previous_value, current_value in zip(
            previous,
            current,
            strict=True,
        ):
            delta = (
                abs(
                    current_value
                    - previous_value
                )
                / 255.0
            )

            delta_total += delta
            maximum_delta = max(
                maximum_delta,
                delta,
            )

            if delta >= self.pixel_threshold:
                changed += 1

        changed_ratio = (
            changed / len(current)
        )

        mean_delta = (
            delta_total / len(current)
        )

        return MotionResult(
            available=True,
            changed_ratio=changed_ratio,
            mean_delta=mean_delta,
            maximum_delta=maximum_delta,
            motion_detected=(
                changed_ratio
                >= self.ratio_threshold
            ),
        )


class FrameTimeline:
    def __init__(self) -> None:
        self._entries: list[
            TimelineEntry
        ] = []

        self._lock = RLock()

    def append(
        self,
        entry: TimelineEntry,
    ) -> TimelineEntry:
        with self._lock:
            self._entries.append(entry)

        return entry

    def list(
        self,
        *,
        media_id: str | None = None,
    ) -> list[TimelineEntry]:
        with self._lock:
            entries = list(self._entries)

        if media_id is None:
            return entries

        return [
            entry
            for entry in entries
            if entry.media_id == media_id
        ]

    def snapshot(self) -> dict[str, Any]:
        entries = self.list()

        return {
            "schema": (
                "sykasif-media-timeline/v1"
            ),
            "entry_count": len(entries),
            "entries": [
                entry.as_dict()
                for entry in entries
            ],
        }


class FrameCache:
    def __init__(
        self,
        *,
        maximum_entries: int = 64,
    ) -> None:
        if maximum_entries <= 0:
            raise ValueError(
                "Önbellek kapasitesi pozitif "
                "olmalıdır."
            )

        self.maximum_entries = (
            maximum_entries
        )

        self._frames: dict[
            str,
            DecodedFrame,
        ] = {}

        self._order: list[str] = []
        self._lock = RLock()

    def put(
        self,
        frame_id: str,
        decoded: DecodedFrame,
    ) -> None:
        with self._lock:
            if frame_id in self._frames:
                self._frames[
                    frame_id
                ] = decoded
                return

            self._frames[
                frame_id
            ] = decoded

            self._order.append(frame_id)

            while (
                len(self._order)
                > self.maximum_entries
            ):
                removed_id = (
                    self._order.pop(0)
                )

                self._frames.pop(
                    removed_id,
                    None,
                )

    def get(
        self,
        frame_id: str,
    ) -> DecodedFrame | None:
        with self._lock:
            return self._frames.get(
                frame_id
            )

    def latest_for_media(
        self,
        entries: list[TimelineEntry],
        media_id: str,
    ) -> DecodedFrame | None:
        matching = [
            entry
            for entry in entries
            if entry.media_id == media_id
        ]

        if not matching:
            return None

        latest = matching[-1]

        return self.get(
            latest.frame_id
        )


class CandidateDTSEAdapter:
    def build_payload(
        self,
        *,
        record: FrameRecord,
        analysis: CandidateAnalysis,
        motion: MotionResult,
    ) -> dict[str, Any]:
        signals = [
            self._signal(candidate)
            for candidate
            in analysis.candidates
        ]

        return {
            "media_id": record.media_id,
            "source_kind": (
                record.source_kind.value
            ),
            "frame_index": (
                record.frame_index
            ),
            "timestamp_ms": (
                record.timestamp_ms
            ),
            "frame_width": (
                record.frame_width
            ),
            "frame_height": (
                record.frame_height
            ),
            "signals": signals,
            "motion": motion.as_dict(),
            "frame_sha256": (
                record.frame_sha256
            ),
            "analysis_scope": (
                "digital_visual_candidates"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }

    def _signal(
        self,
        candidate: FrameCandidate,
    ) -> dict[str, Any]:
        return {
            "label": candidate.label,
            "kind": "anomaly",
            "confidence": min(
                99.9,
                candidate.confidence,
            ),
            "box": candidate.box.as_dict(),
            "description": (
                "Açıklanabilir otomatik "
                "görüntü adayıdır."
            ),
            "metrics": {
                **candidate.metrics,
                "uncertainty": (
                    candidate.uncertainty
                ),
            },
            "evidence_refs": [
                candidate.candidate_id,
                candidate.frame_id,
            ],
            "methods": list(
                candidate.methods
            ),
            "status": "candidate",
        }


class MediaReportAdapter:
    def build_payload(
        self,
        *,
        record: FrameRecord,
        analysis: CandidateAnalysis,
        motion: MotionResult,
    ) -> dict[str, Any]:
        evidences = []

        for candidate in analysis.candidates:
            evidence_sha256 = sha256(
                (
                    record.frame_sha256
                    + candidate.candidate_id
                    + candidate.label
                ).encode("utf-8")
            ).hexdigest()

            evidences.append(
                {
                    "evidence_id": (
                        candidate.candidate_id
                    ),
                    "title": candidate.label,
                    "description": (
                        "Görüntü aday motoru "
                        "tarafından belirlenen "
                        "dijital dikkat bölgesi."
                    ),
                    "confidence": min(
                        99.9,
                        candidate.confidence,
                    ),
                    "status": "candidate",
                    "source": (
                        "frame_candidate_engine"
                    ),
                    "sha256": (
                        evidence_sha256
                    ),
                    "box": (
                        candidate.box.as_dict()
                    ),
                    "methods": list(
                        candidate.methods
                    ),
                }
            )

        return {
            "session_id": record.media_id,
            "title": (
                "SyKaşif Görüntü İncelemesi"
            ),
            "research_type": (
                record.source_kind.value
            ),
            "summary": (
                f"{len(evidences)} dijital "
                "dikkat bölgesi adayı üretildi."
            ),
            "frame": {
                "frame_id": record.frame_id,
                "frame_sha256": (
                    record.frame_sha256
                ),
                "width": record.frame_width,
                "height": record.frame_height,
                "frame_index": (
                    record.frame_index
                ),
                "timestamp_ms": (
                    record.timestamp_ms
                ),
            },
            "motion": motion.as_dict(),
            "evidences": evidences,
            "analysis_scope": (
                "digital_analysis_only"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


class MediaAnalysisPipeline:
    def __init__(
        self,
        *,
        ingestion_engine: (
            FrameIngestionEngine | None
        ) = None,
        candidate_engine: (
            FrameCandidateEngine | None
        ) = None,
        decoder: ImageDecoder | None = None,
        motion_detector: (
            MotionDetector | None
        ) = None,
        timeline: FrameTimeline | None = None,
        cache: FrameCache | None = None,
        dtse_dispatcher: (
            Callable[
                [dict[str, Any]],
                Any,
            ]
            | None
        ) = None,
    ) -> None:
        self.ingestion_engine = (
            ingestion_engine
            or FrameIngestionEngine()
        )

        self.candidate_engine = (
            candidate_engine
            or FrameCandidateEngine(
                minimum_score=0.18
            )
        )

        self.decoder = (
            decoder or ImageDecoder()
        )

        self.motion_detector = (
            motion_detector
            or MotionDetector()
        )

        self.timeline = (
            timeline or FrameTimeline()
        )

        self.cache = (
            cache or FrameCache()
        )

        self.dtse_adapter = (
            CandidateDTSEAdapter()
        )

        self.report_adapter = (
            MediaReportAdapter()
        )

        self.dtse_dispatcher = (
            dtse_dispatcher
        )

    def analyze_image(
        self,
        *,
        media_id: str,
        content: bytes,
        frame_index: int = 0,
        timestamp_ms: int = 0,
        source_kind: str = "image",
        source_name: str = "",
    ) -> MediaAnalysisResult:
        decoded = self.decoder.decode(
            content
        )

        previous = (
            self.cache.latest_for_media(
                self.timeline.list(),
                media_id,
            )
        )

        motion = (
            self.motion_detector.compare(
                (
                    previous.pixels
                    if previous is not None
                    else None
                ),
                decoded.pixels,
            )
        )

        ingestion = (
            self.ingestion_engine.ingest(
                FramePacket(
                    media_id=media_id,
                    source_kind=source_kind,
                    frame_index=frame_index,
                    timestamp_ms=timestamp_ms,
                    frame_width=decoded.width,
                    frame_height=decoded.height,
                    payload=content,
                    source_name=source_name,
                    source_sha256=(
                        decoded.source_sha256
                    ),
                ),
                status="candidate",
            )
        )

        record = ingestion.record

        candidates = (
            self.candidate_engine.analyze(
                record=record,
                pixels=decoded.pixels,
                channels=decoded.channels,
            )
        )

        dtse_payload = (
            self.dtse_adapter.build_payload(
                record=record,
                analysis=candidates,
                motion=motion,
            )
        )

        report_payload = (
            self.report_adapter.build_payload(
                record=record,
                analysis=candidates,
                motion=motion,
            )
        )

        timeline_entry = TimelineEntry(
            media_id=record.media_id,
            frame_id=record.frame_id,
            frame_index=(
                record.frame_index
            ),
            timestamp_ms=(
                record.timestamp_ms
            ),
            source_kind=(
                record.source_kind.value
            ),
            frame_sha256=(
                record.frame_sha256
            ),
            candidate_count=len(
                candidates.candidates
            ),
            motion_detected=(
                motion.motion_detected
            ),
            changed_ratio=(
                motion.changed_ratio
            ),
        )

        if not ingestion.duplicate:
            self.cache.put(
                record.frame_id,
                decoded,
            )

            self.timeline.append(
                timeline_entry
            )

        if (
            self.dtse_dispatcher is not None
            and dtse_payload["signals"]
        ):
            self.dtse_dispatcher(
                dtse_payload
            )

        return MediaAnalysisResult(
            ingestion=ingestion,
            decoded=decoded,
            candidates=candidates,
            motion=motion,
            timeline_entry=(
                timeline_entry
            ),
            dtse_payload=dtse_payload,
            report_payload=report_payload,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-media-pipeline/v1"
            ),
            "frame_registry": (
                self.ingestion_engine
                .snapshot()
            ),
            "timeline": (
                self.timeline.snapshot()
            ),
            "analysis_scope": (
                "digital_media_candidates"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }