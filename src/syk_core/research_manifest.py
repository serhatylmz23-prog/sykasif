"""Araştırma noktası manifest modeli."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .integrity import calculate_payload_sha256
from .persistence_errors import ManifestIntegrityError
from .research_point import ResearchPoint
from .utils import isoformat_utc, utc_now


@dataclass(slots=True, frozen=True)
class ManifestEntry:
    """Manifest içindeki tek dosya veya veri girdisi."""

    entry_id: str
    kind: str
    sha256: str
    size_bytes: int | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.entry_id.strip():
            raise ValueError(
                "Manifest giriş kimliği boş olamaz."
            )

        if not self.kind.strip():
            raise ValueError(
                "Manifest giriş türü boş olamaz."
            )

        if len(self.sha256) != 64:
            raise ValueError(
                "Manifest SHA-256 değeri 64 karakter olmalıdır."
            )

        int(self.sha256, 16)

        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError(
                "Manifest dosya boyutu negatif olamaz."
            )

    def to_dict(self) -> dict[str, Any]:
        """Girdiyi JSON uyumlu sözlüğe dönüştürür."""

        return {
            "entry_id": self.entry_id,
            "kind": self.kind,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "source": self.source,
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ManifestEntry":
        """Sözlükten manifest girdisi oluşturur."""

        return cls(
            entry_id=str(payload["entry_id"]),
            kind=str(payload["kind"]),
            sha256=str(payload["sha256"]),
            size_bytes=(
                None
                if payload.get("size_bytes") is None
                else int(payload["size_bytes"])
            ),
            source=payload.get("source"),
        )


@dataclass(slots=True)
class ResearchManifest:
    """Araştırma noktası ve bağlı kanıtların bütünlük manifesti."""

    entity_id: str
    snapshot_sha256: str
    history_last_hash: str
    entries: tuple[ManifestEntry, ...]
    generated_at: datetime = field(default_factory=utc_now)
    manifest_version: str = "1.0"
    manifest_sha256: str | None = None

    def __post_init__(self) -> None:
        self.entity_id = self.entity_id.strip()

        if not self.entity_id:
            raise ValueError(
                "Manifest varlık kimliği boş olamaz."
            )

        for name, digest in (
            ("snapshot_sha256", self.snapshot_sha256),
            ("history_last_hash", self.history_last_hash),
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
            raise ManifestIntegrityError(
                "Manifest SHA-256 değeri geçersiz."
            )

    def unsigned_payload(self) -> dict[str, Any]:
        """Manifest hash hesabına giren alanları döndürür."""

        return {
            "manifest_version": self.manifest_version,
            "entity_id": self.entity_id,
            "generated_at": isoformat_utc(self.generated_at),
            "snapshot_sha256": self.snapshot_sha256,
            "history_last_hash": self.history_last_hash,
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ],
        }

    def calculate_hash(self) -> str:
        """Manifest SHA-256 değerini hesaplar."""

        return calculate_payload_sha256(
            self.unsigned_payload()
        )

    def verify(self) -> bool:
        """Manifest kendi bütünlüğünü doğrular."""

        return self.manifest_sha256 == self.calculate_hash()

    def assert_valid(self) -> None:
        """Manifest bozuksa istisna üretir."""

        if not self.verify():
            raise ManifestIntegrityError(
                "Manifest bütünlüğü doğrulanamadı."
            )

    def to_dict(self) -> dict[str, Any]:
        """Manifesti JSON uyumlu sözlüğe dönüştürür."""

        return {
            **self.unsigned_payload(),
            "manifest_sha256": self.manifest_sha256,
        }

    @classmethod
    def from_point(
        cls,
        point: ResearchPoint,
        *,
        snapshot_sha256: str,
        history_last_hash: str,
    ) -> "ResearchManifest":
        """Araştırma noktasından manifest üretir."""

        entries: list[ManifestEntry] = []

        for evidence in point.evidence.values():
            if evidence.sha256_digest is None:
                continue

            entries.append(
                ManifestEntry(
                    entry_id=evidence.identity.syk_id or "",
                    kind=evidence.kind.value,
                    sha256=evidence.sha256_digest,
                    size_bytes=evidence.size_bytes,
                    source=(
                        evidence.local_path
                        or evidence.source_uri
                    ),
                )
            )

        entries.sort(
            key=lambda item: item.entry_id
        )

        return cls(
            entity_id=point.identity.syk_id or "",
            snapshot_sha256=snapshot_sha256,
            history_last_hash=history_last_hash,
            entries=tuple(entries),
        )

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ResearchManifest":
        """Sözlükten manifest oluşturur."""

        from .deserialization import parse_datetime

        generated_at = parse_datetime(
            payload.get("generated_at")
        )

        if generated_at is None:
            raise ManifestIntegrityError(
                "Manifest üretim zamanı bulunamadı."
            )

        return cls(
            manifest_version=str(
                payload.get("manifest_version", "1.0")
            ),
            entity_id=str(payload["entity_id"]),
            generated_at=generated_at,
            snapshot_sha256=str(
                payload["snapshot_sha256"]
            ),
            history_last_hash=str(
                payload["history_last_hash"]
            ),
            entries=tuple(
                ManifestEntry.from_dict(item)
                for item in payload.get("entries") or []
            ),
            manifest_sha256=str(
                payload["manifest_sha256"]
            ),
        )
