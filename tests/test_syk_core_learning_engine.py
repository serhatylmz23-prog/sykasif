from __future__ import annotations

import pytest

from syk_core.learning import (
    ApprovalDecision,
    CandidateStatus,
    ImpactLevel,
    LearningClaim,
    ModelRevisionRegistry,
    ResearchSource,
    ResearchUpdateEngine,
    SourceTrustEngine,
    SourceTrustLevel,
    UpdateType,
)


def create_authoritative_source() -> ResearchSource:
    return ResearchSource(
        source_id="SRC-RESMÎ-001",
        title="Türkiye Tatlı Su Türleri Güncellemesi",
        publisher="Yetkili Bilimsel Kurum",
        source_type="official_report",
        authority_score=95,
        methodology_score=92,
        transparency_score=90,
        corroboration_score=88,
        recency_score=96,
        peer_reviewed=True,
        official_source=True,
        primary_source=True,
    )


def create_weak_source() -> ResearchSource:
    return ResearchSource(
        source_id="SRC-ZAYIF-001",
        title="Kaynağı Belirsiz Tür Listesi",
        publisher="Belirsiz Yayıncı",
        source_type="social_post",
        authority_score=20,
        methodology_score=15,
        transparency_score=10,
        corroboration_score=10,
        recency_score=70,
        conflict_of_interest=True,
    )


def create_claim() -> LearningClaim:
    return LearningClaim(
        claim_id="CLM-BALIK-001",
        statement=(
            "Fırat Turnası tür kaydı Keban Baraj Gölü "
            "katmanında güncellenmelidir."
        ),
        subject_type="fish_species",
        subject_id="FISH-FIRAT-TURNASI",
        old_value={
            "durum": "inceleme_bekliyor",
        },
        proposed_value={
            "durum": "kaynakla_desteklendi",
        },
        supporting_source_ids={
            "SRC-RESMÎ-001",
        },
        confidence_score=91.0,
    )


def test_authoritative_source_is_accepted() -> None:
    engine = SourceTrustEngine()

    result = engine.evaluate(
        create_authoritative_source()
    )

    assert result.accepted is True
    assert result.score >= 90
    assert (
        result.level
        == SourceTrustLevel.AUTHORITATIVE
    )


def test_weak_source_is_rejected() -> None:
    engine = SourceTrustEngine()

    result = engine.evaluate(
        create_weak_source()
    )

    assert result.accepted is False
    assert result.score < 55
    assert result.warnings


def test_candidate_without_accepted_source_needs_evidence() -> None:
    engine = ResearchUpdateEngine()

    result = engine.create_candidate(
        title="Zayıf Kaynak Güncellemesi",
        update_type=UpdateType.NEW_INFORMATION,
        sources=(
            create_weak_source(),
        ),
        claims=(
            LearningClaim(
                claim_id="CLM-ZAYIF-001",
                statement="Doğrulanmamış yeni bilgi.",
                subject_type="plant_species",
                confidence_score=40.0,
            ),
        ),
        proposed_changes={
            "plant_species.status": "new",
        },
    )

    assert (
        result.candidate.status
        == CandidateStatus.NEEDS_EVIDENCE
    )
    assert (
        result.candidate.accepted_source_count
        == 0
    )


def test_candidate_with_valid_source_is_sent_to_review() -> None:
    engine = ResearchUpdateEngine()

    result = engine.create_candidate(
        title="Keban Balık Katmanı Güncellemesi",
        update_type=UpdateType.TAXONOMY_UPDATE,
        sources=(
            create_authoritative_source(),
        ),
        claims=(
            create_claim(),
        ),
        proposed_changes={
            "fish_species.FISH-FIRAT-TURNASI.status": (
                "kaynakla_desteklendi"
            ),
        },
        affected_entity_ids={
            "FISH-FIRAT-TURNASI",
        },
        affected_layer_codes={
            "fish_species",
            "sonar",
        },
    )

    assert (
        result.candidate.status
        == CandidateStatus.NEEDS_REVIEW
    )
    assert result.candidate.confidence_score >= 80
    assert (
        result.assessment.overall_level
        == ImpactLevel.HIGH
    )
    assert (
        result.assessment
        .requires_regression_test
        is True
    )


def test_contradiction_reduces_confidence() -> None:
    claim = create_claim()
    claim.contradicting_source_ids.add(
        "SRC-ÇELİŞKİ-001"
    )

    engine = ResearchUpdateEngine()

    result = engine.create_candidate(
        title="Çelişkili Tür Güncellemesi",
        update_type=UpdateType.CONTRADICTION,
        sources=(
            create_authoritative_source(),
        ),
        claims=(claim,),
        proposed_changes={
            "fish_species.status": "review",
        },
    )

    assert (
        result.candidate.contradiction_count
        == 1
    )
    assert (
        result.candidate.status
        == CandidateStatus.NEEDS_REVIEW
    )
    assert result.assessment.warnings


def test_human_approval_is_required_before_apply() -> None:
    engine = ResearchUpdateEngine()

    result = engine.create_candidate(
        title="Bitki Katmanı Güncellemesi",
        update_type=UpdateType.REGIONAL_UPDATE,
        sources=(
            create_authoritative_source(),
        ),
        claims=(
            LearningClaim(
                claim_id="CLM-BİTKİ-001",
                statement=(
                    "Bölgesel bitki katmanı yeniden değerlendirilmelidir."
                ),
                subject_type="plant_species",
                supporting_source_ids={
                    "SRC-RESMÎ-001",
                },
                confidence_score=90.0,
            ),
        ),
        proposed_changes={
            "plant_layer.region": "updated",
        },
        affected_layer_codes={
            "vegetation",
            "botanical",
        },
    )

    with pytest.raises(ValueError):
        engine.apply(
            result,
            applied_by="Kurucu Kaan",
        )


def test_approved_candidate_creates_revision() -> None:
    engine = ResearchUpdateEngine()

    result = engine.create_candidate(
        title="Keban Balık Türü Güncellemesi",
        update_type=UpdateType.TAXONOMY_UPDATE,
        sources=(
            create_authoritative_source(),
        ),
        claims=(
            create_claim(),
        ),
        proposed_changes={
            "fish_species.FISH-FIRAT-TURNASI.status": (
                "kaynakla_desteklendi"
            ),
        },
        affected_entity_ids={
            "FISH-FIRAT-TURNASI",
        },
        affected_layer_codes={
            "fish_species",
        },
    )

    engine.review(
        result,
        reviewer_id="Bilge Kaan",
        decision=ApprovalDecision.APPROVE,
        comment=(
            "Kaynak, iddia ve etki analizi incelendi."
        ),
    )

    engine.apply(
        result,
        applied_by="Kurucu Kaan",
    )

    assert result.applied is True
    assert (
        result.candidate.status
        == CandidateStatus.APPLIED
    )
    assert result.revision is not None
    assert result.revision.verify() is True
    assert result.revision.version == 1


def test_rejected_candidate_cannot_be_applied() -> None:
    engine = ResearchUpdateEngine()

    result = engine.create_candidate(
        title="Reddedilecek Güncelleme",
        update_type=UpdateType.NEW_INFORMATION,
        sources=(
            create_authoritative_source(),
        ),
        claims=(
            create_claim(),
        ),
        proposed_changes={
            "temporary": True,
        },
    )

    engine.review(
        result,
        reviewer_id="Bilge Kaan",
        decision=ApprovalDecision.REJECT,
        comment="Kanıt kapsamı yeterli görülmedi.",
    )

    assert (
        result.candidate.status
        == CandidateStatus.REJECTED
    )

    with pytest.raises(ValueError):
        engine.apply(
            result,
            applied_by="Kurucu Kaan",
        )


def test_revision_registry_supports_rollback() -> None:
    registry = ModelRevisionRegistry()

    first = registry.apply(
        candidate_id="SYK-LRN-001",
        changes={
            "value": 1,
        },
        applied_by="Kurucu",
    )

    second = registry.apply(
        candidate_id="SYK-LRN-002",
        changes={
            "value": 2,
        },
        applied_by="Kurucu",
    )

    rollback = registry.rollback(
        revision_id=first.revision_id,
        applied_by="Kurucu",
        reason="İkinci sürüm geri alındı.",
    )

    assert second.active is False
    assert rollback.active is True
    assert (
        rollback.rollback_of_revision_id
        == first.revision_id
    )
    assert rollback.changes == {
        "value": 1,
    }
    assert registry.current is rollback
