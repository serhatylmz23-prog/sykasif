from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4


SOURCE_KINDS = {
    "image",
    "video",
    "live",
}

SIGNAL_KINDS = {
    "object",
    "surface",
    "texture",
    "thermal",
    "spectral",
    "geometry",
    "motion",
    "symbol",
    "anomaly",
}

STATE_PALETTES = {
    "verified": {
        "primary": "#6DFF41",
        "secondary": "#B8FF9F",
    },
    "analyzing": {
        "primary": "#37DFFF",
        "secondary": "#A9F3FF",
    },
    "review": {
        "primary": "#FFD640",
        "secondary": "#FFF0A0",
    },
    "low_confidence": {
        "primary": "#FF9D1A",
        "secondary": "#FFD19A",
    },
    "rare_anomaly": {
        "primary": "#B86CFF",
        "secondary": "#E0BFFF",
    },
}


@dataclass(frozen=True)
class NormalizedBox:
    x: float
    y: float
    width: float
    height: float

    def validate(self) -> None:
        values = (
            self.x,
            self.y,
            self.width,
            self.height,
        )

        if any(
            value < 0.0 or value > 1.0
            for value in values
        ):
            raise ValueError(
                "Kutu değerleri 0.0 ile 1.0 arasında olmalıdır."
            )

        if self.width <= 0.0 or self.height <= 0.0:
            raise ValueError(
                "Kutu genişliği ve yüksekliği sıfırdan büyük olmalıdır."
            )

        if self.x + self.width > 1.0:
            raise ValueError(
                "Kutu görüntü genişliği dışına taşıyor."
            )

        if self.y + self.height > 1.0:
            raise ValueError(
                "Kutu görüntü yüksekliği dışına taşıyor."
            )

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> dict[str, float]:
        return {
            "x": self.x + self.width / 2.0,
            "y": self.y + self.height / 2.0,
        }


@dataclass(frozen=True)
class AttentionSignal:
    label: str
    kind: str
    confidence: float
    box: NormalizedBox
    description: str = ""
    metrics: dict[str, Any] | None = None
    evidence_refs: list[str] | None = None

    def validate(self) -> None:
        if not self.label.strip():
            raise ValueError(
                "Dikkat sinyali etiketi boş olamaz."
            )

        if self.kind not in SIGNAL_KINDS:
            raise ValueError(
                f"Bilinmeyen dikkat sinyali türü: {self.kind}"
            )

        if not 0.0 <= self.confidence <= 99.9:
            raise ValueError(
                "Dijital güven 0.0 ile 99.9 arasında olmalıdır."
            )

        self.box.validate()


class DTSEAttentionEngine:
    def __init__(
        self,
        *,
        minimum_confidence: float = 60.0,
        minimum_area: float = 0.0004,
        duplicate_window_frames: int = 12,
    ) -> None:
        self._minimum_confidence = minimum_confidence
        self._minimum_area = minimum_area
        self._duplicate_window_frames = (
            duplicate_window_frames
        )

        self._events: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []
        self._signatures: dict[str, int] = {}
        self._sequence = 0
        self._lock = RLock()

    @property
    def sequence(self) -> int:
        return self._sequence

    def ingest(
        self,
        *,
        media_id: str,
        source_kind: str,
        frame_index: int,
        timestamp_ms: int,
        frame_width: int,
        frame_height: int,
        signals: list[AttentionSignal],
    ) -> dict[str, Any]:
        if source_kind not in SOURCE_KINDS:
            raise ValueError(
                f"Bilinmeyen kaynak türü: {source_kind}"
            )

        if not media_id.strip():
            raise ValueError(
                "Medya kimliği boş olamaz."
            )

        if frame_index < 0:
            raise ValueError(
                "Kare numarası negatif olamaz."
            )

        if timestamp_ms < 0:
            raise ValueError(
                "Zaman değeri negatif olamaz."
            )

        if frame_width <= 0 or frame_height <= 0:
            raise ValueError(
                "Geçerli kare ölçüleri gereklidir."
            )

        created = []
        ignored = []

        with self._lock:
            for signal in signals:
                signal.validate()

                reason = self._ignore_reason(signal)

                if reason is not None:
                    ignored.append(
                        {
                            "label": signal.label,
                            "reason": reason,
                        }
                    )
                    continue

                signature = self._signature(
                    media_id=media_id,
                    signal=signal,
                )

                previous_frame = self._signatures.get(
                    signature
                )

                if (
                    previous_frame is not None
                    and frame_index - previous_frame
                    <= self._duplicate_window_frames
                ):
                    ignored.append(
                        {
                            "label": signal.label,
                            "reason": "duplicate_window",
                        }
                    )
                    continue

                event = self._build_event(
                    media_id=media_id,
                    source_kind=source_kind,
                    frame_index=frame_index,
                    timestamp_ms=timestamp_ms,
                    frame_width=frame_width,
                    frame_height=frame_height,
                    signal=signal,
                )

                self._events[event["id"]] = event
                self._order.append(event["id"])
                self._signatures[signature] = frame_index
                self._sequence += 1

                created.append(event)

        return {
            "media_id": media_id,
            "source_kind": source_kind,
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms,
            "created_count": len(created),
            "ignored_count": len(ignored),
            "events": created,
            "ignored": ignored,
            "sequence": self._sequence,
        }

    def inventory(
        self,
        *,
        media_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._lock:
            event_ids = list(
                reversed(self._order)
            )

            result = []

            for event_id in event_ids:
                event = self._events[event_id]

                if (
                    media_id is not None
                    and event["media_id"] != media_id
                ):
                    continue

                result.append(event)

                if len(result) >= limit:
                    break

            return result

    def get(
        self,
        event_id: str,
    ) -> dict[str, Any]:
        try:
            return self._events[event_id]
        except KeyError as error:
            raise KeyError(event_id) from error

    def snapshot(self) -> dict[str, Any]:
        events = self.inventory(limit=50)

        return {
            "sequence": self._sequence,
            "event_count": len(self._events),
            "latest_event": (
                events[0]
                if events
                else None
            ),
            "events": events,
        }

    def _ignore_reason(
        self,
        signal: AttentionSignal,
    ) -> str | None:
        if signal.confidence < self._minimum_confidence:
            return "confidence_below_threshold"

        if signal.box.area < self._minimum_area:
            return "region_too_small"

        return None

    def _state(
        self,
        signal: AttentionSignal,
    ) -> str:
        if (
            signal.kind == "anomaly"
            and signal.confidence >= 85.0
        ):
            return "rare_anomaly"

        if signal.confidence >= 95.0:
            return "verified"

        if signal.confidence >= 80.0:
            return "analyzing"

        if signal.confidence >= 70.0:
            return "review"

        return "low_confidence"

    def _build_event(
        self,
        *,
        media_id: str,
        source_kind: str,
        frame_index: int,
        timestamp_ms: int,
        frame_width: int,
        frame_height: int,
        signal: AttentionSignal,
    ) -> dict[str, Any]:
        state = self._state(signal)
        palette = STATE_PALETTES[state]

        box = asdict(signal.box)
        center = signal.box.center

        connector_target = {
            "x": min(
                0.96,
                signal.box.x
                + signal.box.width
                + 0.12,
            ),
            "y": max(
                0.08,
                min(0.92, center["y"]),
            ),
        }

        visual_layer = {
            "type": "dtse_attention_layer",
            "coordinate_space": "normalized",
            "box": box,
            "center": center,
            "corner_style": "crescent_curve",
            "corner_radius": min(
                signal.box.width,
                signal.box.height,
            ) * 0.18,
            "border_style": "dotted",
            "connector": {
                "style": "dotted",
                "from": {
                    "x": (
                        signal.box.x
                        + signal.box.width
                    ),
                    "y": center["y"],
                },
                "to": connector_target,
            },
            "palette": palette,
            "pulse": (
                state in {
                    "rare_anomaly",
                    "analyzing",
                }
            ),
            "label_anchor": connector_target,
        }

        unsigned = {
            "id": str(uuid4()),
            "schema": (
                "sykasif-dtse-attention-event/v1"
            ),
            "media_id": media_id,
            "source_kind": source_kind,
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms,
            "frame": {
                "width": frame_width,
                "height": frame_height,
            },
            "signal": {
                "label": signal.label,
                "kind": signal.kind,
                "description": signal.description,
                "confidence": round(
                    min(99.9, signal.confidence),
                    3,
                ),
                "metrics": signal.metrics or {},
                "evidence_refs": (
                    signal.evidence_refs or []
                ),
            },
            "syframe": {
                "state": state,
                "confidence": round(
                    min(99.9, signal.confidence),
                    3,
                ),
                "requires_review": True,
            },
            "visual_layer": visual_layer,
            "analysis": {
                "status": "queued",
                "requested_modules": (
                    self._analysis_modules(
                        signal.kind
                    )
                ),
                "field_validation_required": True,
            },
            "created_at": datetime.now(
                UTC
            ).isoformat(),
        }

        return {
            **unsigned,
            "event_sha256": self._hash(unsigned),
        }

    def _analysis_modules(
        self,
        kind: str,
    ) -> list[str]:
        mapping = {
            "object": [
                "image",
                "history",
                "archaeology",
            ],
            "surface": [
                "dtse",
                "geometry",
                "material",
            ],
            "texture": [
                "dtse",
                "spectral",
                "material",
            ],
            "thermal": [
                "thermal",
                "dtse",
            ],
            "spectral": [
                "spectral",
                "chemical",
                "material",
            ],
            "geometry": [
                "dtse",
                "measurement",
                "lidar",
            ],
            "motion": [
                "video",
                "tracking",
            ],
            "symbol": [
                "image",
                "history",
                "archaeology",
            ],
            "anomaly": [
                "dtse",
                "syframe",
                "cross_validation",
            ],
        }

        return mapping[kind]

    def _signature(
        self,
        *,
        media_id: str,
        signal: AttentionSignal,
    ) -> str:
        rounded = {
            "media_id": media_id,
            "label": signal.label,
            "kind": signal.kind,
            "x": round(signal.box.x, 2),
            "y": round(signal.box.y, 2),
            "width": round(
                signal.box.width,
                2,
            ),
            "height": round(
                signal.box.height,
                2,
            ),
        }

        return self._hash(rounded)

    def _hash(
        self,
        payload: dict[str, Any],
    ) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(
            canonical
        ).hexdigest()