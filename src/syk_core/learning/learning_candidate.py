"""Öğrenme adayı ve iddia modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import fmean
from typing import Any
from uuid import uuid4

from ..utils import json_safe, utc_now
from .enums import (
    CandidateStatus,
    UpdateType,
)
from .source_trust import (
    ResearchSource,
    SourceTrustResult,
)


@dataclass(slots=True)
class LearningClaim:
    """Araştırma güncellemesindeki tek doğrulanabilir iddia."""

    claim_id: str
    statement: str
    subject_type: str
    subject_id: str | None = None
    old_value: Any = None
    proposed_value: Any = None
    supporting_source_ids: set[str] = field(
        default_factory=set
    )
    contradicting_source_ids: set[str] = field(
        default_factory=set
    )
    confidence_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.claim_id = self.claim_id.strip()
        self.statement = self.statement.strip()
        self.subject_type = self.subject_type.strip()

        if not self.claim_id:
            raise ValueError("İddia kimliği boş olamaz.")

        if not self.statement:
            raise ValueError("İddia metni boş olamaz.")

        if not self.subject_type:
            raise ValueError("İddia konu türü boş olamaz.")

        self.confidence_score = float(
            self.confidence_score
        )

        if not 0.0 <= self.confidence_score <= 100.0:
            raise ValueError(
                "İddia güven skoru 0 ile 100 arasında olmalıdır."
            )

    @property
    def has_contradiction(self) -> bool:
        return bool(self.contradicting_source_ids)

    @property
    def support_count(self) -> int:
        return len(self.supporting_source_ids)

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "claim_id": self.claim_id,
                "statement": self.statement,
                "subject_type": self.subject_type,
                "subject_id": self.subject_id,
                "old_value": self.old_value,
                "proposed_value": self.proposed_value,
                "supporting_source_ids": sorted(
                    self.supporting_source_ids
                ),
                "contradicting_source_ids": sorted(
                    self.contradicting_source_ids
                ),
                "confidence_score": self.confidence_score,
                "has_contradiction": self.has_contradiction,
                "metadata": self.metadata,
            }
        )


@dataclass(slots=True)
class LearningCandidate:
    """Kalıcı modele uygulanmadan önce incelenecek öğrenme adayı."""

    title: str
    update_type: UpdateType
    candidate_id: str = field(
        default_factory=lambda: (
            f"SYK-LRN-{uuid4().hex[:16].upper()}"
        )
    )
    description: str | None = None
    status: CandidateStatus = CandidateStatus.NEW
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    sources: dict[str, ResearchSource] = field(
        default_factory=dict
    )
    source_results: dict[str, SourceTrustResult] = field(
        default_factory=dict
    )
    claims: dict[str, LearningClaim] = field(
        default_factory=dict
    )
    affected_entity_ids: set[str] = field(
        default_factory=set
    )
    affected_layer_codes: set[str] = field(
        default_factory=set
    )
    proposed_changes: dict[str, Any] = field(
        default_factory=dict
    )
    confidence_score: float = 0.0
    requires_human_approval: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.candidate_id = self.candidate_id.strip()

        if not self.title:
            raise ValueError(
                "Öğrenme adayı başlığı boş olamaz."
            )

        if not self.candidate_id:
            raise ValueError(
                "Öğrenme adayı kimliği boş olamaz."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()

    def add_source(
        self,
        source: ResearchSource,
        result: SourceTrustResult,
    ) -> None:
        if source.source_id != result.source_id:
            raise ValueError(
                "Kaynak ile güven sonucu kimliği eşleşmiyor."
            )

        self.sources[source.source_id] = source
        self.source_results[source.source_id] = result
        self.touch()

    def add_claim(
        self,
        claim: LearningClaim,
    ) -> None:
        if claim.claim_id in self.claims:
            raise ValueError(
                f"İddia zaten kayıtlı: {claim.claim_id}"
            )

        self.claims[claim.claim_id] = claim
        self.touch()

    @property
    def accepted_source_count(self) -> int:
        return sum(
            1
            for result in self.source_results.values()
            if result.accepted
        )

    @property
    def rejected_source_count(self) -> int:
        return sum(
            1
            for result in self.source_results.values()
            if not result.accepted
        )

    @property
    def contradiction_count(self) -> int:
        return sum(
            1
            for claim in self.claims.values()
            if claim.has_contradiction
        )

    def recalculate_confidence(self) -> float:
        accepted_scores = [
            result.score
            for result in self.source_results.values()
            if result.accepted
        ]

        claim_scores = [
            claim.confidence_score
            for claim in self.claims.values()
        ]

        if not accepted_scores and not claim_scores:
            self.confidence_score = 0.0
            return self.confidence_score

        source_score = (
            fmean(accepted_scores)
            if accepted_scores
            else 0.0
        )

        claim_score = (
            fmean(claim_scores)
            if claim_scores
            else 0.0
        )

        if accepted_scores and claim_scores:
            combined = (
                source_score * 0.55
                + claim_score * 0.45
            )
        elif accepted_scores:
            combined = source_score
        else:
            combined = claim_score * 0.75

        contradiction_penalty = min(
            30.0,
            self.contradiction_count * 8.0,
        )

        weak_source_penalty = min(
            20.0,
            self.rejected_source_count * 3.0,
        )

        self.confidence_score = round(
            max(
                0.0,
                combined
                - contradiction_penalty
                - weak_source_penalty,
            ),
            3,
        )

        self.touch()

        return self.confidence_score

    def determine_status(self) -> CandidateStatus:
        self.recalculate_confidence()

        if self.accepted_source_count == 0:
            self.status = CandidateStatus.NEEDS_EVIDENCE
        elif self.contradiction_count > 0:
            self.status = CandidateStatus.NEEDS_REVIEW
        elif self.confidence_score < 60:
            self.status = CandidateStatus.NEEDS_EVIDENCE
        else:
            self.status = CandidateStatus.NEEDS_REVIEW

        self.touch()

        return self.status

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "candidate_id": self.candidate_id,
                "title": self.title,
                "description": self.description,
                "update_type": self.update_type,
                "status": self.status,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "sources": [
                    source.to_dict()
                    for source in self.sources.values()
                ],
                "source_results": [
                    result.to_dict()
                    for result in self.source_results.values()
                ],
                "claims": [
                    claim.to_dict()
                    for claim in self.claims.values()
                ],
                "affected_entity_ids": sorted(
                    self.affected_entity_ids
                ),
                "affected_layer_codes": sorted(
                    self.affected_layer_codes
                ),
                "proposed_changes": self.proposed_changes,
                "confidence_score": self.confidence_score,
                "requires_human_approval": (
                    self.requires_human_approval
                ),
                "accepted_source_count": (
                    self.accepted_source_count
                ),
                "rejected_source_count": (
                    self.rejected_source_count
                ),
                "contradiction_count": (
                    self.contradiction_count
                ),
                "metadata": self.metadata,
            }
        )
