"""Öğrenen araştırma motoru numaralandırmaları."""

from __future__ import annotations

from enum import StrEnum


class SourceTrustLevel(StrEnum):
    """Kaynağın güven seviyesi."""

    UNKNOWN = "unknown"
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    AUTHORITATIVE = "authoritative"


class CandidateStatus(StrEnum):
    """Öğrenme adayının yaşam döngüsü."""

    NEW = "new"
    ANALYZING = "analyzing"
    NEEDS_EVIDENCE = "needs_evidence"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ApprovalDecision(StrEnum):
    """İnsan onay kapısı kararı."""

    PENDING = "pending"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_EVIDENCE = "request_evidence"
    REQUEST_REVISION = "request_revision"


class ImpactLevel(StrEnum):
    """Güncellemenin sistem üzerindeki etkisi."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UpdateType(StrEnum):
    """Araştırma güncellemesinin türü."""

    NEW_INFORMATION = "new_information"
    CORRECTION = "correction"
    CONTRADICTION = "contradiction"
    SOURCE_UPDATE = "source_update"
    TAXONOMY_UPDATE = "taxonomy_update"
    LAYER_UPDATE = "layer_update"
    MODEL_RULE_UPDATE = "model_rule_update"
    REGIONAL_UPDATE = "regional_update"
    SEASONAL_UPDATE = "seasonal_update"
    SAFETY_UPDATE = "safety_update"
