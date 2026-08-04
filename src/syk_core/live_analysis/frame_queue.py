"""Fotoğraf ve video kare kuyruğu."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..ecosystem import ObservationSource
from ..location import GeoLocation
from ..utils import json_safe, utc_now
from .enums import FrameProcessingState


class FrameQueueError(Exception):
    """Kare kuyruğu ana hatası."""


class FrameQueueFullError(FrameQueueError):
    """Kare kuyruğu dolu."""


class FrameQueueEmptyError(FrameQueueError):
    """Kare kuyruğu boş."""


@dataclass(slots=True)
class AnalysisFrame:
    """Canlı kamera, fotoğraf veya video karesi."""

    source: ObservationSource
    location: GeoLocation
    frame_id: str = field(
        default_factory=lambda: (
            f"SYK-FRM-{uuid4().hex[:16].upper()}"
        )
    )
    captured_at: datetime = field(default_factory=utc_now)
    source_uri: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    sequence_number: int | None = None
    state: FrameProcessingState = FrameProcessingState.QUEUED
    retry_count: int = 0
    evidence_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.frame_id = self.frame_id.strip()

        if not self.frame_id:
            raise ValueError(
                "Kare kimliği boş olamaz."
            )

        for name in (
            "width_px",
            "height_px",
            "sequence_number",
            "retry_count",
        ):
            value = getattr(self, name)

            if value is not None and int(value) < 0:
                raise ValueError(
                    f"{name} negatif olamaz."
                )

    def mark_processing(self) -> None:
        self.state = FrameProcessingState.PROCESSING

    def mark_analyzed(self) -> None:
        self.state = FrameProcessingState.ANALYZED

    def mark_rejected(
        self,
        reason: str,
    ) -> None:
        self.state = FrameProcessingState.REJECTED
        self.metadata["rejection_reason"] = reason.strip()

    def mark_failed(
        self,
        error_message: str,
    ) -> None:
        self.state = FrameProcessingState.FAILED
        self.retry_count += 1
        self.metadata["last_error"] = error_message.strip()

    def archive(self) -> None:
        self.state = FrameProcessingState.ARCHIVED

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "frame_id": self.frame_id,
                "source": self.source,
                "location": self.location.to_dict(),
                "captured_at": self.captured_at,
                "source_uri": self.source_uri,
                "width_px": self.width_px,
                "height_px": self.height_px,
                "sequence_number": self.sequence_number,
                "state": self.state,
                "retry_count": self.retry_count,
                "evidence_ids": sorted(self.evidence_ids),
                "metadata": self.metadata,
            }
        )


class FrameQueue:
    """Sınırlı kapasiteli canlı analiz kare kuyruğu."""

    def __init__(
        self,
        *,
        capacity: int = 120,
    ) -> None:
        if capacity < 1:
            raise ValueError(
                "Kuyruk kapasitesi en az 1 olmalıdır."
            )

        self.capacity = capacity
        self._queue: deque[AnalysisFrame] = deque()
        self._known_ids: set[str] = set()

    def enqueue(
        self,
        frame: AnalysisFrame,
    ) -> None:
        if len(self._queue) >= self.capacity:
            raise FrameQueueFullError(
                "Canlı analiz kare kuyruğu dolu."
            )

        if frame.frame_id in self._known_ids:
            raise ValueError(
                f"Kare zaten kuyrukta: {frame.frame_id}"
            )

        frame.state = FrameProcessingState.QUEUED
        self._queue.append(frame)
        self._known_ids.add(frame.frame_id)

    def dequeue(self) -> AnalysisFrame:
        if not self._queue:
            raise FrameQueueEmptyError(
                "Canlı analiz kare kuyruğu boş."
            )

        frame = self._queue.popleft()
        self._known_ids.discard(frame.frame_id)
        frame.mark_processing()

        return frame

    def peek(self) -> AnalysisFrame:
        if not self._queue:
            raise FrameQueueEmptyError(
                "Canlı analiz kare kuyruğu boş."
            )

        return self._queue[0]

    def clear(self) -> tuple[AnalysisFrame, ...]:
        frames = tuple(self._queue)
        self._queue.clear()
        self._known_ids.clear()

        return frames

    @property
    def remaining_capacity(self) -> int:
        return self.capacity - len(self._queue)

    def __len__(self) -> int:
        return len(self._queue)

    def __contains__(
        self,
        frame_id: object,
    ) -> bool:
        return frame_id in self._known_ids
