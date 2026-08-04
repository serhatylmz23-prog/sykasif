"""Canlı analiz manifest modeli."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..integrity import calculate_payload_sha256
from ..utils import isoformat_utc, json_safe, utc_now
from .snapshot import LiveSessionSnapshot


@dataclass(slots=True, frozen=True)
class LiveManifestEntry:
    """Canlı analiz manifestindeki tek kayıt."""

    entry_id: str
    entry_type: str
    sha256: str
    related_id: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.entry_id.strip():
            raise ValueError(
                "Manifest giriş kimliği boş olamaz."
            )

        if not self.entry_type.strip():
            raise ValueError(
                "Manifest giriş türü boş olamaz."
            )

        if len(self.sha256) != 64:
            raise ValueError(
                "Manifest giriş SHA-256 değeri 64 karakter olmalıdır."
            )

        int(self.sha256, 16)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "sha256": self.sha256,
            "related_id": self.related_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "LiveManifestEntry":
        return cls(
            entry_id=str(payload["entry_id"]),
            entry_type=str(
                payload["entry_type"]
            ),
            sha256=str(payload["sha256"]),
            related_id=payload.get(
                "related_id"
            ),
            metadata=dict(
                payload.get("metadata") or {}
            ),
        )


@dataclass(slots=True)
class LiveAnalysisManifest:
    """Canlı analiz oturumunun bütünlük manifesti."""

    session_id: str
    snapshot_sha256: str
    audit_last_hash: str
    entries: tuple[
        LiveManifestEntry,
        ...,
    ]
    generated_at: datetime = field(default_factory=utc_now)
    manifest_version: str = "1.0"
    manifest_sha256: str | None = None

    def __post_init__(self) -> None:
        self.session_id = self.session_id.strip()

        if not self.session_id:
            raise ValueError(
                "Manifest oturum kimliği boş olamaz."
            )

        for name, digest in (
            (
                "snapshot_sha256",
                self.snapshot_sha256,
            ),
            (
                "audit_last_hash",
                self.audit_last_hash,
            ),
        ):
            if len(digest) != 64:
                raise ValueError(
                    f"{name} 64 karakter olmalıdır."
                )

            int(digest, 16)

        calculated = self.calculate_hash()

        if self.manifest_sha256 is None:
            self.manifest_sha256 = calculated
        elif self.manifest_sha256 != calculated:
            raise ValueError(
                "Canlı analiz manifest SHA-256 değeri geçersiz."
            )

    def unsigned_payload(self) -> dict[str, Any]:
        return json_safe(
            {
                "manifest_version": (
                    self.manifest_version
                ),
                "session_id": self.session_id,
                "generated_at": isoformat_utc(
                    self.generated_at
                ),
                "snapshot_sha256": (
                    self.snapshot_sha256
                ),
                "audit_last_hash": (
                    self.audit_last_hash
                ),
                "entries": [
                    entry.to_dict()
                    for entry in self.entries
                ],
            }
        )

    def calculate_hash(self) -> str:
        return calculate_payload_sha256(
            self.unsigned_payload()
        )

    def verify(self) -> bool:
        return (
            self.manifest_sha256
            == self.calculate_hash()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.unsigned_payload(),
            "manifest_sha256": (
                self.manifest_sha256
            ),
        }

    @classmethod
    def from_snapshot(
        cls,
        *,
        snapshot: LiveSessionSnapshot,
        snapshot_sha256: str,
        audit_last_hash: str,
    ) -> "LiveAnalysisManifest":
        entries: list[LiveManifestEntry] = []

        for record in (
            snapshot.history_records
        ):
            record_id = str(
                record["record_id"]
            )

            entries.append(
                LiveManifestEntry(
                    entry_id=record_id,
                    entry_type="detection",
                    sha256=(
                        calculate_payload_sha256(
                            record
                        )
                    ),
                    related_id=record.get(
                        "frame_id"
                    ),
                    metadata={
                        "entity_type": record.get(
                            "entity_type"
                        ),
                        "species_id": record.get(
                            "species_id"
                        ),
                    },
                )
            )

        return cls(
            session_id=snapshot.session_id,
            snapshot_sha256=(
                snapshot_sha256
            ),
            audit_last_hash=(
                audit_last_hash
            ),
            entries=tuple(
                sorted(
                    entries,
                    key=lambda item: (
                        item.entry_id
                    ),
                )
            ),
        )

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "LiveAnalysisManifest":
        from ..deserialization import parse_datetime

        generated_at = parse_datetime(
            payload.get("generated_at")
        )

        if generated_at is None:
            raise ValueError(
                "Manifest üretim zamanı bulunamadı."
            )

        return cls(
            manifest_version=str(
                payload.get(
                    "manifest_version",
                    "1.0",
                )
            ),
            session_id=str(
                payload["session_id"]
            ),
            generated_at=generated_at,
            snapshot_sha256=str(
                payload["snapshot_sha256"]
            ),
            audit_last_hash=str(
                payload["audit_last_hash"]
            ),
            entries=tuple(
                LiveManifestEntry.from_dict(
                    item
                )
                for item in (
                    payload.get("entries")
                    or []
                )
            ),
            manifest_sha256=str(
                payload["manifest_sha256"]
            ),
        )
