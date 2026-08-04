"""Canlı analiz numaralandırmaları."""

from __future__ import annotations

from enum import StrEnum


class LiveSessionState(StrEnum):
    """Canlı analiz oturumu durumu."""

    CREATED = "created"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class FrameProcessingState(StrEnum):
    """Kamera veya video karesi işleme durumu."""

    QUEUED = "queued"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    REJECTED = "rejected"
    FAILED = "failed"
    ARCHIVED = "archived"


class DetectionState(StrEnum):
    """Canlı tespit durumu."""

    NEW = "new"
    TRACKING = "tracking"
    CLASSIFIED = "classified"
    REVIEW_REQUIRED = "review_required"
    VERIFIED = "verified"
    LOST = "lost"
    REJECTED = "rejected"


class MapPinState(StrEnum):
    """Dinamik harita pini durumu."""

    NEW = "new"
    ACTIVE = "active"
    CLUSTERED = "clustered"
    REVIEW_REQUIRED = "review_required"
    VERIFIED = "verified"
    HIDDEN = "hidden"
    ARCHIVED = "archived"
