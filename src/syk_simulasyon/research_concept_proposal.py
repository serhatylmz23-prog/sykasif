from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable

from .hedef_sicili import HedefAilesi, KaynakNiteligi


class ProposalStatus(StrEnum):
    CANDIDATE = "candidate"
    REVIEW_REQUIRED = "review_required"
    INSUFFICIENT_DATA = "insufficient_data"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ResearchEvidence:
    source_id: str
    source_quality: KaynakNiteligi
    support_score: float
    claim: str
    uncertainty_note: str | None = None
    contradicts: bool = False

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("Kaynak kimli?i bo? olamaz")

        if not self.claim.strip():
            raise ValueError("Kan?t a??klamas? bo? olamaz")

        if not 0.0 <= self.support_score <= 1.0:
            raise ValueError(
                "Destek puan? 0 ile 1 aras?nda olmal?d?r"
            )


@dataclass(frozen=True)
class ConceptCandidate:
    concept_name: str
    family: HedefAilesi
    description: str
    evidence: tuple[ResearchEvidence, ...]
    unknown_fields: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.concept_name.strip():
            raise ValueError("Kavram ad? bo? olamaz")

        if not self.description.strip():
            raise ValueError("A??klama bo? olamaz")


@dataclass(frozen=True)
class ResearchConceptProposal:
    proposal_id: str
    internal_fingerprint: str
    concept_name: str
    family: HedefAilesi
    confidence_score: float
    uncertainty_score: float
    priority_score: float
    status: ProposalStatus
    evidence_count: int
    contradiction_count: int
    unknown_fields: tuple[str, ...]
    user_explanation: str
    requires_bilge_kaan_review: bool = True
    automatic_approval_allowed: bool = False

    def to_internal_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "internal_fingerprint": self.internal_fingerprint,
            "concept_name": self.concept_name,
            "family": self.family,
            "confidence_score": self.confidence_score,
            "uncertainty_score": self.uncertainty_score,
            "priority_score": self.priority_score,
            "status": self.status,
            "evidence_count": self.evidence_count,
            "contradiction_count": self.contradiction_count,
            "unknown_fields": self.unknown_fields,
            "user_explanation": self.user_explanation,
            "requires_bilge_kaan_review": (
                self.requires_bilge_kaan_review
            ),
            "automatic_approval_allowed": (
                self.automatic_approval_allowed
            ),
        }


_SOURCE_WEIGHTS: dict[KaynakNiteligi, float] = {
    KaynakNiteligi.BIRINCIL_BILIMSEL: 0.95,
    KaynakNiteligi.RESMI_TEKNIK: 0.90,
    KaynakNiteligi.IKINCIL_BILIMSEL: 0.78,
    KaynakNiteligi.UZMAN_GORUSU: 0.65,
    KaynakNiteligi.SIMULASYON_VARSAYIMI: 0.40,
    KaynakNiteligi.DOGRULANMAMIS: 0.10,
}


@dataclass
class ResearchConceptProposalEngine:
    review_threshold: float = 0.60
    minimum_evidence_count: int = 1
    known_fingerprints: set[str] = field(
        default_factory=set
    )

    def propose(
        self,
        candidate: ConceptCandidate,
    ) -> ResearchConceptProposal:
        fingerprint = self._fingerprint(candidate)

        if fingerprint in self.known_fingerprints:
            return self._duplicate_proposal(
                candidate,
                fingerprint,
            )

        evidence_count = len(candidate.evidence)

        contradiction_count = sum(
            item.contradicts
            for item in candidate.evidence
        )

        confidence = self._confidence(
            candidate.evidence
        )

        uncertainty = self._uncertainty(
            evidence_count=evidence_count,
            contradiction_count=contradiction_count,
            unknown_count=len(candidate.unknown_fields),
        )

        priority = round(
            min(
                1.0,
                confidence * 0.45
                + uncertainty * 0.35
                + min(
                    1.0,
                    evidence_count / 5.0,
                )
                * 0.20,
            ),
            4,
        )

        status = self._status(
            confidence,
            evidence_count,
            contradiction_count,
        )

        proposal = ResearchConceptProposal(
            proposal_id=self._opaque_id(),
            internal_fingerprint=fingerprint,
            concept_name=candidate.concept_name.strip(),
            family=candidate.family,
            confidence_score=confidence,
            uncertainty_score=uncertainty,
            priority_score=priority,
            status=status,
            evidence_count=evidence_count,
            contradiction_count=contradiction_count,
            unknown_fields=tuple(
                candidate.unknown_fields
            ),
            user_explanation=self._user_explanation(
                candidate,
                confidence,
                contradiction_count,
            ),
        )

        self.known_fingerprints.add(fingerprint)

        return proposal

    def propose_many(
        self,
        candidates: Iterable[ConceptCandidate],
    ) -> list[ResearchConceptProposal]:
        proposals = [
            self.propose(candidate)
            for candidate in candidates
        ]

        proposals.sort(
            key=lambda item: (
                -item.priority_score,
                item.proposal_id,
            )
        )

        return proposals

    @staticmethod
    def _confidence(
        evidence_items: tuple[
            ResearchEvidence,
            ...,
        ],
    ) -> float:
        if not evidence_items:
            return 0.0

        weighted_total = 0.0
        weight_total = 0.0

        for item in evidence_items:
            weight = _SOURCE_WEIGHTS[
                item.source_quality
            ]

            direction = (
                -1.0
                if item.contradicts
                else 1.0
            )

            weighted_total += (
                item.support_score
                * weight
                * direction
            )

            weight_total += weight

        return round(
            max(
                0.0,
                min(
                    1.0,
                    weighted_total / weight_total,
                ),
            ),
            4,
        )

    @staticmethod
    def _uncertainty(
        evidence_count: int,
        contradiction_count: int,
        unknown_count: int,
    ) -> float:
        evidence_gap = max(
            0.0,
            1.0
            - min(
                1.0,
                evidence_count / 4.0,
            ),
        )

        contradiction_effect = min(
            0.70,
            contradiction_count * 0.35,
        )

        unknown_effect = min(
            0.40,
            unknown_count * 0.08,
        )

        return round(
            min(
                1.0,
                evidence_gap
                + contradiction_effect
                + unknown_effect,
            ),
            4,
        )

    def _status(
        self,
        confidence: float,
        evidence_count: int,
        contradiction_count: int,
    ) -> ProposalStatus:
        if (
            evidence_count
            < self.minimum_evidence_count
        ):
            return (
                ProposalStatus.INSUFFICIENT_DATA
            )

        if (
            contradiction_count > 0
            or confidence
            >= self.review_threshold
        ):
            return ProposalStatus.REVIEW_REQUIRED

        return ProposalStatus.CANDIDATE

    @staticmethod
    def _fingerprint(
        candidate: ConceptCandidate,
    ) -> str:
        payload = {
            "concept_name": (
                candidate.concept_name
                .strip()
                .casefold()
            ),
            "family": candidate.family,
            "description": (
                candidate.description
                .strip()
                .casefold()
            ),
            "source_ids": sorted(
                item.source_id
                for item in candidate.evidence
            ),
        }

        return hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _opaque_id() -> str:
        return secrets.token_hex(12).upper()

    @staticmethod
    def _user_explanation(
        candidate: ConceptCandidate,
        confidence: float,
        contradiction_count: int,
    ) -> str:
        if not candidate.evidence:
            return (
                "Kavram ara?t?rma aday? olarak "
                "kaydedildi. De?erlendirme i?in "
                "kaynak verisi gereklidir."
            )

        if contradiction_count:
            return (
                f"Kavram?n destek d?zeyi "
                f"%{confidence * 100:.1f}. "
                f"{contradiction_count} ?eli?en "
                "kay?t bulundu?u i?in Bilge Kaan "
                "incelemesi gereklidir."
            )

        return (
            f"Kavram?n destek d?zeyi "
            f"%{confidence * 100:.1f}. "
            "Bu sonu? kesin h?k?m de?ildir; "
            "ara?t?rma ?nerisi olarak Bilge Kaan "
            "incelemesine sunulur."
        )

    @staticmethod
    def _duplicate_proposal(
        candidate: ConceptCandidate,
        fingerprint: str,
    ) -> ResearchConceptProposal:
        return ResearchConceptProposal(
            proposal_id=(
                ResearchConceptProposalEngine
                ._opaque_id()
            ),
            internal_fingerprint=fingerprint,
            concept_name=(
                candidate.concept_name.strip()
            ),
            family=candidate.family,
            confidence_score=0.0,
            uncertainty_score=1.0,
            priority_score=0.0,
            status=ProposalStatus.REJECTED,
            evidence_count=len(
                candidate.evidence
            ),
            contradiction_count=sum(
                item.contradicts
                for item in candidate.evidence
            ),
            unknown_fields=tuple(
                candidate.unknown_fields
            ),
            user_explanation=(
                "Ayn? ara?t?rma kavram? daha "
                "?nce kaydedildi. Yinelenen "
                "?neri reddedildi."
            ),
        )
