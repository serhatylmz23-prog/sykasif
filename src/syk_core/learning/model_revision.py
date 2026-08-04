"""Model sürümleme ve geri alma."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..integrity import calculate_payload_sha256
from ..utils import json_safe, utc_now


class RevisionNotFoundError(KeyError):
    """Model sürümü bulunamadı."""


@dataclass(slots=True)
class ModelRevision:
    """Onaylanan öğrenme güncellemesinin model sürümü."""

    candidate_id: str
    version: int
    changes: dict[str, Any]
    applied_by: str
    revision_id: str = field(
        default_factory=lambda: (
            f"SYK-REV-{uuid4().hex[:16].upper()}"
        )
    )
    created_at: datetime = field(default_factory=utc_now)
    parent_revision_id: str | None = None
    rollback_of_revision_id: str | None = None
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    revision_sha256: str | None = None

    def __post_init__(self) -> None:
        self.candidate_id = self.candidate_id.strip()
        self.applied_by = self.applied_by.strip()

        if not self.candidate_id:
            raise ValueError(
                "Sürüm aday kimliği boş olamaz."
            )

        if not self.applied_by:
            raise ValueError(
                "Sürümü uygulayan kullanıcı boş olamaz."
            )

        if self.version < 1:
            raise ValueError(
                "Model sürüm numarası en az 1 olmalıdır."
            )

        calculated = self.calculate_hash()

        if self.revision_sha256 is None:
            self.revision_sha256 = calculated
        elif self.revision_sha256 != calculated:
            raise ValueError(
                "Model sürümü SHA-256 değeri geçersiz."
            )

    def unsigned_payload(self) -> dict[str, Any]:
        return json_safe(
            {
                "revision_id": self.revision_id,
                "candidate_id": self.candidate_id,
                "version": self.version,
                "changes": self.changes,
                "applied_by": self.applied_by,
                "created_at": self.created_at,
                "parent_revision_id": (
                    self.parent_revision_id
                ),
                "rollback_of_revision_id": (
                    self.rollback_of_revision_id
                ),
                "active": self.active,
                "metadata": self.metadata,
            }
        )

    def calculate_hash(self) -> str:
        return calculate_payload_sha256(
            self.unsigned_payload()
        )

    def verify(self) -> bool:
        return (
            self.revision_sha256
            == self.calculate_hash()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.unsigned_payload(),
            "revision_sha256": self.revision_sha256,
        }


class ModelRevisionRegistry:
    """Model sürümlerini ve geri alma zincirini yönetir."""

    def __init__(self) -> None:
        self._revisions: list[ModelRevision] = []

    @property
    def current(
        self,
    ) -> ModelRevision | None:
        active = [
            revision
            for revision in self._revisions
            if revision.active
        ]

        if not active:
            return None

        return active[-1]

    def apply(
        self,
        *,
        candidate_id: str,
        changes: dict[str, Any],
        applied_by: str,
        metadata: dict[str, Any] | None = None,
    ) -> ModelRevision:
        current = self.current

        if current is not None:
            current.active = False
            current.revision_sha256 = (
                current.calculate_hash()
            )

        revision = ModelRevision(
            candidate_id=candidate_id,
            version=len(self._revisions) + 1,
            changes=dict(changes),
            applied_by=applied_by,
            parent_revision_id=(
                current.revision_id
                if current is not None
                else None
            ),
            metadata=dict(metadata or {}),
        )

        self._revisions.append(revision)

        return revision

    def rollback(
        self,
        *,
        revision_id: str,
        applied_by: str,
        reason: str,
    ) -> ModelRevision:
        target = self.get(revision_id)

        current = self.current

        if current is not None:
            current.active = False
            current.revision_sha256 = (
                current.calculate_hash()
            )

        rollback_revision = ModelRevision(
            candidate_id=target.candidate_id,
            version=len(self._revisions) + 1,
            changes=dict(target.changes),
            applied_by=applied_by,
            parent_revision_id=(
                current.revision_id
                if current is not None
                else None
            ),
            rollback_of_revision_id=(
                target.revision_id
            ),
            metadata={
                "rollback_reason": reason.strip(),
            },
        )

        self._revisions.append(
            rollback_revision
        )

        return rollback_revision

    def get(
        self,
        revision_id: str,
    ) -> ModelRevision:
        for revision in self._revisions:
            if revision.revision_id == revision_id:
                return revision

        raise RevisionNotFoundError(
            f"Model sürümü bulunamadı: {revision_id}"
        )

    def all(
        self,
    ) -> tuple[ModelRevision, ...]:
        return tuple(self._revisions)
