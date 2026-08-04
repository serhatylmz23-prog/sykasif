"""İnsan onay kapısı."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..utils import json_safe, utc_now
from .enums import (
    ApprovalDecision,
    CandidateStatus,
)
from .impact_analysis import ImpactAssessment
from .learning_candidate import LearningCandidate


@dataclass(slots=True)
class ApprovalRecord:
    """Öğrenme adayı için insan kararı."""

    candidate_id: str
    reviewer_id: str
    decision: ApprovalDecision
    comment: str
    approval_id: str = field(
        default_factory=lambda: (
            f"SYK-APR-{uuid4().hex[:16].upper()}"
        )
    )
    created_at: datetime = field(default_factory=utc_now)
    conditions: tuple[str, ...] = tuple()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.candidate_id = self.candidate_id.strip()
        self.reviewer_id = self.reviewer_id.strip()
        self.comment = self.comment.strip()

        if not self.candidate_id:
            raise ValueError(
                "Onay kaydı aday kimliği boş olamaz."
            )

        if not self.reviewer_id:
            raise ValueError(
                "Onaylayan kullanıcı kimliği boş olamaz."
            )

        if not self.comment:
            raise ValueError(
                "Onay açıklaması boş olamaz."
            )

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "approval_id": self.approval_id,
                "candidate_id": self.candidate_id,
                "reviewer_id": self.reviewer_id,
                "decision": self.decision,
                "comment": self.comment,
                "created_at": self.created_at,
                "conditions": list(self.conditions),
                "metadata": self.metadata,
            }
        )


class ApprovalGate:
    """Kalıcı öğrenmeyi insan kararına bağlar."""

    def __init__(self) -> None:
        self._records: dict[
            str,
            list[ApprovalRecord],
        ] = {}

    def review(
        self,
        *,
        candidate: LearningCandidate,
        assessment: ImpactAssessment,
        reviewer_id: str,
        decision: ApprovalDecision,
        comment: str,
        conditions: tuple[str, ...] = tuple(),
    ) -> ApprovalRecord:
        if assessment.candidate_id != candidate.candidate_id:
            raise ValueError(
                "Etki analizi ile öğrenme adayı eşleşmiyor."
            )

        if decision == ApprovalDecision.PENDING:
            raise ValueError(
                "Beklemede kararı nihai inceleme kararı değildir."
            )

        if (
            decision == ApprovalDecision.APPROVE
            and candidate.accepted_source_count == 0
        ):
            raise ValueError(
                "Güvenilir kaynak bulunmadan aday onaylanamaz."
            )

        if (
            decision == ApprovalDecision.APPROVE
            and candidate.confidence_score < 60
        ):
            raise ValueError(
                "Güven skoru 60 altında olan aday onaylanamaz."
            )

        record = ApprovalRecord(
            candidate_id=candidate.candidate_id,
            reviewer_id=reviewer_id,
            decision=decision,
            comment=comment,
            conditions=conditions,
            metadata={
                "impact_level": (
                    assessment.overall_level.value
                ),
                "confidence_score": (
                    candidate.confidence_score
                ),
            },
        )

        self._records.setdefault(
            candidate.candidate_id,
            [],
        ).append(record)

        if decision == ApprovalDecision.APPROVE:
            candidate.status = CandidateStatus.APPROVED
        elif decision == ApprovalDecision.REJECT:
            candidate.status = CandidateStatus.REJECTED
        elif decision == ApprovalDecision.REQUEST_EVIDENCE:
            candidate.status = CandidateStatus.NEEDS_EVIDENCE
        elif decision == ApprovalDecision.REQUEST_REVISION:
            candidate.status = CandidateStatus.NEEDS_REVIEW

        candidate.touch()

        return record

    def records_for(
        self,
        candidate_id: str,
    ) -> tuple[ApprovalRecord, ...]:
        return tuple(
            self._records.get(
                candidate_id,
                [],
            )
        )

    def latest_for(
        self,
        candidate_id: str,
    ) -> ApprovalRecord | None:
        records = self._records.get(
            candidate_id,
            [],
        )

        if not records:
            return None

        return records[-1]
