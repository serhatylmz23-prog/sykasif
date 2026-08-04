"""SyKaşif öğrenen araştırma çalışma motoru."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .approval_gate import (
    ApprovalGate,
    ApprovalRecord,
)
from .enums import (
    ApprovalDecision,
    CandidateStatus,
    UpdateType,
)
from .impact_analysis import (
    ImpactAnalysisEngine,
    ImpactAssessment,
)
from .learning_candidate import (
    LearningCandidate,
    LearningClaim,
)
from .model_revision import (
    ModelRevision,
    ModelRevisionRegistry,
)
from .source_trust import (
    ResearchSource,
    SourceTrustEngine,
)


@dataclass(slots=True)
class ResearchUpdateResult:
    """Araştırma güncellemesi değerlendirme sonucu."""

    candidate: LearningCandidate
    assessment: ImpactAssessment
    approval: ApprovalRecord | None = None
    revision: ModelRevision | None = None

    @property
    def applied(self) -> bool:
        return (
            self.revision is not None
            and self.candidate.status
            == CandidateStatus.APPLIED
        )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "öğrenme_adayı": (
                self.candidate.to_dict()
            ),
            "etki_analizi": (
                self.assessment.to_dict()
            ),
            "onay": (
                self.approval.to_dict()
                if self.approval is not None
                else None
            ),
            "model_sürümü": (
                self.revision.to_dict()
                if self.revision is not None
                else None
            ),
            "uygulandı": self.applied,
        }


class ResearchUpdateEngine:
    """Kaynakları değerlendirir, adayı oluşturur ve onaya sunar."""

    def __init__(
        self,
        *,
        trust_engine: SourceTrustEngine | None = None,
        impact_engine: ImpactAnalysisEngine | None = None,
        approval_gate: ApprovalGate | None = None,
        revision_registry: ModelRevisionRegistry | None = None,
    ) -> None:
        self.trust_engine = (
            trust_engine
            or SourceTrustEngine()
        )
        self.impact_engine = (
            impact_engine
            or ImpactAnalysisEngine()
        )
        self.approval_gate = (
            approval_gate
            or ApprovalGate()
        )
        self.revision_registry = (
            revision_registry
            or ModelRevisionRegistry()
        )

    def create_candidate(
        self,
        *,
        title: str,
        update_type: UpdateType,
        sources: tuple[ResearchSource, ...],
        claims: tuple[LearningClaim, ...],
        proposed_changes: dict[str, Any],
        affected_entity_ids: set[str] | None = None,
        affected_layer_codes: set[str] | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchUpdateResult:
        candidate = LearningCandidate(
            title=title,
            description=description,
            update_type=update_type,
            proposed_changes=dict(
                proposed_changes
            ),
            affected_entity_ids=set(
                affected_entity_ids or set()
            ),
            affected_layer_codes=set(
                affected_layer_codes or set()
            ),
            metadata=dict(metadata or {}),
        )

        candidate.status = CandidateStatus.ANALYZING

        for source in sources:
            trust_result = self.trust_engine.evaluate(
                source
            )

            candidate.add_source(
                source,
                trust_result,
            )

        for claim in claims:
            candidate.add_claim(claim)

        candidate.determine_status()

        assessment = self.impact_engine.analyze(
            candidate
        )

        return ResearchUpdateResult(
            candidate=candidate,
            assessment=assessment,
        )

    def review(
        self,
        result: ResearchUpdateResult,
        *,
        reviewer_id: str,
        decision: ApprovalDecision,
        comment: str,
        conditions: tuple[str, ...] = tuple(),
    ) -> ResearchUpdateResult:
        approval = self.approval_gate.review(
            candidate=result.candidate,
            assessment=result.assessment,
            reviewer_id=reviewer_id,
            decision=decision,
            comment=comment,
            conditions=conditions,
        )

        result.approval = approval

        return result

    def apply(
        self,
        result: ResearchUpdateResult,
        *,
        applied_by: str,
    ) -> ResearchUpdateResult:
        if result.approval is None:
            raise ValueError(
                "Öğrenme adayı onaylanmadan uygulanamaz."
            )

        if (
            result.approval.decision
            != ApprovalDecision.APPROVE
        ):
            raise ValueError(
                "Yalnız onaylanan öğrenme adayı uygulanabilir."
            )

        if (
            result.candidate.status
            != CandidateStatus.APPROVED
        ):
            raise ValueError(
                "Öğrenme adayı onaylı durumda değil."
            )

        revision = self.revision_registry.apply(
            candidate_id=(
                result.candidate.candidate_id
            ),
            changes=(
                result.candidate.proposed_changes
            ),
            applied_by=applied_by,
            metadata={
                "impact_level": (
                    result.assessment
                    .overall_level
                    .value
                ),
                "confidence_score": (
                    result.candidate
                    .confidence_score
                ),
                "manifest_update_required": (
                    result.assessment
                    .requires_manifest_update
                ),
                "regression_test_required": (
                    result.assessment
                    .requires_regression_test
                ),
            },
        )

        result.candidate.status = (
            CandidateStatus.APPLIED
        )
        result.candidate.touch()
        result.revision = revision

        return result
