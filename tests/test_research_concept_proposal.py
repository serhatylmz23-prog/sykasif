import re

from syk_simulasyon.hedef_sicili import (
    HedefAilesi,
    KaynakNiteligi,
)
from syk_simulasyon.research_concept_proposal import (
    ConceptCandidate,
    ProposalStatus,
    ResearchConceptProposalEngine,
    ResearchEvidence,
)


def _arsenic_bronze_candidate():
    return ConceptCandidate(
        concept_name="Arsenik bronz",
        family=HedefAilesi.MALZEME,
        description=(
            "Bak?r esasl? ve arsenik i?eren "
            "ara?t?rma kavram?."
        ),
        evidence=(
            ResearchEvidence(
                source_id="7A91F3C2",
                source_quality=(
                    KaynakNiteligi
                    .BIRINCIL_BILIMSEL
                ),
                support_score=0.88,
                claim=(
                    "Kimyasal bile?im bak?r "
                    "ve arsenik i?eriyor."
                ),
            ),
            ResearchEvidence(
                source_id="31D8B509",
                source_quality=(
                    KaynakNiteligi
                    .IKINCIL_BILIMSEL
                ),
                support_score=0.72,
                claim=(
                    "Malzeme arsenik i?eren "
                    "bak?r ala??m? olabilir."
                ),
                uncertainty_note=(
                    "Y?zey korozyonu "
                    "de?erlendirilmelidir."
                ),
            ),
        ),
        unknown_fields=(
            "?retim y?ntemi",
            "y?zey korozyon etkisi",
        ),
        tags=(
            "bak?r",
            "arsenik",
            "ala??m",
        ),
    )


def test_supported_concept_requires_review():
    proposal = (
        ResearchConceptProposalEngine()
        .propose(
            _arsenic_bronze_candidate()
        )
    )

    assert (
        proposal.status
        == ProposalStatus.REVIEW_REQUIRED
    )

    assert (
        proposal.requires_bilge_kaan_review
        is True
    )

    assert (
        proposal.automatic_approval_allowed
        is False
    )

    assert proposal.confidence_score > 0.70


def test_external_id_has_no_semantic_prefix():
    proposal = (
        ResearchConceptProposalEngine()
        .propose(
            _arsenic_bronze_candidate()
        )
    )

    assert re.fullmatch(
        r"[0-9A-F]{24}",
        proposal.proposal_id,
    )

    assert all(
        prefix not in proposal.proposal_id
        for prefix in (
            "AR",
            "AK",
            "MAT",
        )
    )


def test_conflict_increases_uncertainty():
    engine = ResearchConceptProposalEngine()
    base = _arsenic_bronze_candidate()

    conflicting = ConceptCandidate(
        concept_name=base.concept_name,
        family=base.family,
        description=(
            base.description
            + " ?eli?ki testi."
        ),
        evidence=base.evidence
        + (
            ResearchEvidence(
                source_id="A18C4F70",
                source_quality=(
                    KaynakNiteligi
                    .RESMI_TEKNIK
                ),
                support_score=0.80,
                claim=(
                    "?l??m y?zey bula????ndan "
                    "kaynaklanabilir."
                ),
                contradicts=True,
            ),
        ),
        unknown_fields=base.unknown_fields,
    )

    base_result = engine.propose(base)

    conflict_result = engine.propose(
        conflicting
    )

    assert (
        conflict_result.uncertainty_score
        > base_result.uncertainty_score
    )

    assert (
        conflict_result.status
        == ProposalStatus.REVIEW_REQUIRED
    )


def test_candidate_without_evidence():
    proposal = (
        ResearchConceptProposalEngine()
        .propose(
            ConceptCandidate(
                concept_name=(
                    "Bilinmeyen malzeme"
                ),
                family=HedefAilesi.MALZEME,
                description=(
                    "Kayna?? hen?z "
                    "bulunmam?? aday."
                ),
                evidence=(),
            )
        )
    )

    assert (
        proposal.status
        == ProposalStatus.INSUFFICIENT_DATA
    )

    assert proposal.confidence_score == 0.0

    assert (
        proposal.automatic_approval_allowed
        is False
    )


def test_duplicate_candidate_is_rejected():
    engine = ResearchConceptProposalEngine()
    candidate = _arsenic_bronze_candidate()

    first = engine.propose(candidate)
    second = engine.propose(candidate)

    assert (
        first.status
        != ProposalStatus.REJECTED
    )

    assert (
        second.status
        == ProposalStatus.REJECTED
    )

    assert second.priority_score == 0.0


def test_user_explanation_is_turkish_only():
    proposal = (
        ResearchConceptProposalEngine()
        .propose(
            _arsenic_bronze_candidate()
        )
    )

    assert (
        "Bilge Kaan incelemesine"
        in proposal.user_explanation
    )

    assert (
        "research"
        not in proposal.user_explanation.lower()
    )

    assert (
        "review"
        not in proposal.user_explanation.lower()
    )
