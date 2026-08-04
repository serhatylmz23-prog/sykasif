from __future__ import annotations

import json
from pathlib import Path

import pytest

from syk_core import (
    AccuracySource,
    EntityStatus,
    EvidenceKind,
    EvidenceRecord,
    GeoLocation,
    JsonResearchPointRepository,
    LayerCategory,
    LayerRecord,
    ResearchCategory,
    ResearchPoint,
    ResearchPointAlreadyExistsError,
    ResearchPointNotFoundError,
)


def create_point(
    tmp_path: Path,
) -> ResearchPoint:
    point = ResearchPoint(
        title="Kalıcı Kayıt Araştırma Noktası",
        description="JSON depo doğrulama kaydı.",
        location=GeoLocation(
            latitude=37.2234,
            longitude=38.9221,
            altitude_m=742.5,
            horizontal_accuracy_m=0.018,
            accuracy_source=AccuracySource.RTK_FIXED,
        ),
        category=ResearchCategory.ARCHAEOLOGY,
        priority=92,
        tags={
            "arkeoloji",
            "kalıcı-kayıt",
        },
    )

    geological_layer = LayerRecord(
        name="Jeolojik Formasyon",
        category=LayerCategory.GEOLOGY,
        visible=True,
        opacity=0.68,
        priority=90,
        metadata={
            "catalog_code": "geology",
        },
    )

    point.add_layer(geological_layer)

    evidence_path = tmp_path / "kanit.bin"
    evidence_path.write_bytes(
        b"SYK-PERSISTENCE-EVIDENCE"
    )

    evidence = EvidenceRecord(
        title="Kalıcı Kanıt",
        kind=EvidenceKind.DOCUMENT,
    )
    evidence.attach_local_file(
        evidence_path,
        mime_type="application/octet-stream",
    )
    assert evidence.verify_local_file() is True

    point.add_evidence(evidence)
    point.transition_to(EntityStatus.ACTIVE)

    return point


def test_repository_save_and_load_roundtrip(
    tmp_path: Path,
) -> None:
    repository = JsonResearchPointRepository(
        tmp_path / "repository"
    )
    point = create_point(tmp_path)
    entity_id = point.identity.syk_id or ""

    manifest = repository.save(
        point,
        actor="Bilge Kaan",
    )
    loaded = repository.load(entity_id)

    assert repository.exists(entity_id)
    assert loaded.identity.syk_id == entity_id
    assert loaded.title == point.title
    assert loaded.category == point.category
    assert loaded.status == EntityStatus.ACTIVE
    assert len(loaded.layers) == 1
    assert len(loaded.evidence) == 1
    assert manifest.entity_id == entity_id
    assert manifest.verify() is True
    assert repository.verify(entity_id) is True


def test_repository_rejects_existing_without_replace(
    tmp_path: Path,
) -> None:
    repository = JsonResearchPointRepository(
        tmp_path / "repository"
    )
    point = create_point(tmp_path)

    repository.save(point)

    with pytest.raises(
        ResearchPointAlreadyExistsError
    ):
        repository.save(
            point,
            replace=False,
        )


def test_repository_list_and_delete(
    tmp_path: Path,
) -> None:
    repository = JsonResearchPointRepository(
        tmp_path / "repository"
    )
    point = create_point(tmp_path)
    entity_id = point.identity.syk_id or ""

    repository.save(point)

    assert entity_id in repository.list_ids()

    repository.delete(entity_id)

    assert entity_id not in repository.list_ids()

    with pytest.raises(
        ResearchPointNotFoundError
    ):
        repository.load(entity_id)


def test_save_update_creates_second_history_event(
    tmp_path: Path,
) -> None:
    repository = JsonResearchPointRepository(
        tmp_path / "repository"
    )
    point = create_point(tmp_path)
    entity_id = point.identity.syk_id or ""

    repository.save(
        point,
        actor="Kurucu",
    )

    point.add_tag("güncellendi")
    point.metadata["revision"] = 2

    repository.save(
        point,
        actor="Kurucu",
    )

    history = repository.load_history(entity_id)

    assert len(history.events) == 2
    assert history.events[0].sequence == 1
    assert history.events[1].sequence == 2
    assert (
        history.events[1].previous_hash
        == history.events[0].event_hash
    )
    assert history.verify() is True
    assert (
        history.events[0].action
        == "research_point_created"
    )
    assert (
        history.events[1].action
        == "research_point_updated"
    )


def test_snapshot_tampering_is_detected(
    tmp_path: Path,
) -> None:
    repository = JsonResearchPointRepository(
        tmp_path / "repository"
    )
    point = create_point(tmp_path)
    entity_id = point.identity.syk_id or ""

    repository.save(point)

    point_path = (
        repository.points_directory
        / f"{entity_id}.json"
    )

    payload = json.loads(
        point_path.read_text(
            encoding="utf-8"
        )
    )
    payload["payload"]["title"] = (
        "Yetkisiz Değişiklik"
    )

    point_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    from syk_core import RepositoryIntegrityError

    with pytest.raises(
        RepositoryIntegrityError
    ):
        repository.load(entity_id)


def test_missing_point_raises_not_found(
    tmp_path: Path,
) -> None:
    repository = JsonResearchPointRepository(
        tmp_path / "repository"
    )

    with pytest.raises(
        ResearchPointNotFoundError
    ):
        repository.load(
            "SYK-RP-MISSING"
        )
