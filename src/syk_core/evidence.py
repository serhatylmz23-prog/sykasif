"""Kanıt kayıt modeli ve dosya bütünlüğü."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from .constants import EVIDENCE_PREFIX, HASH_ALGORITHM
from .enums import (
    EvidenceKind,
    EvidenceStatus,
    VerificationLevel,
)
from .errors import EvidenceIntegrityError
from .identity import EntityIdentity
from .utils import json_safe, normalize_text, utc_now


def calculate_file_sha256(
    path: str | Path,
    *,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Dosyanın SHA-256 değerini bellek dostu biçimde hesaplar."""

    file_path = Path(path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Kanıt dosyası bulunamadı: {file_path}"
        )

    digest = sha256()

    with file_path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


@dataclass(slots=True)
class EvidenceRecord:
    """Araştırma noktasına bağlı doğrulanabilir kanıt."""

    title: str
    kind: EvidenceKind
    identity: EntityIdentity = field(
        default_factory=lambda: EntityIdentity(EVIDENCE_PREFIX)
    )
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    verification_level: VerificationLevel = (
        VerificationLevel.UNVERIFIED
    )
    source_uri: str | None = None
    local_path: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256_digest: str | None = None
    collected_at: datetime = field(default_factory=utc_now)
    verified_at: datetime | None = None
    collector_id: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.title = normalize_text(
            self.title,
            field_name="evidence.title",
        )

        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError(
                "Kanıt dosya boyutu negatif olamaz."
            )

        if self.sha256_digest is not None:
            self.sha256_digest = self._normalize_digest(
                self.sha256_digest
            )

        if (
            self.verification_level
            != VerificationLevel.UNVERIFIED
            and self.status == EvidenceStatus.REJECTED
        ):
            raise ValueError(
                "Reddedilmiş kanıt doğrulanmış olamaz."
            )

    @staticmethod
    def _normalize_digest(value: str) -> str:
        digest = value.strip().lower()

        if len(digest) != 64:
            raise EvidenceIntegrityError(
                "SHA-256 değeri 64 onaltılık karakter olmalıdır."
            )

        try:
            int(digest, 16)
        except ValueError as exc:
            raise EvidenceIntegrityError(
                "SHA-256 değeri geçersiz karakter içeriyor."
            ) from exc

        return digest

    @property
    def has_integrity_hash(self) -> bool:
        """Kanıtın bütünlük özeti bulunup bulunmadığını döndürür."""

        return self.sha256_digest is not None

    def attach_local_file(
        self,
        path: str | Path,
        *,
        mime_type: str | None = None,
    ) -> None:
        """Yerel dosyayı kanıta bağlar ve SHA-256 üretir."""

        file_path = Path(path)

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Kanıt dosyası bulunamadı: {file_path}"
            )

        self.local_path = str(file_path.resolve())
        self.size_bytes = file_path.stat().st_size
        self.sha256_digest = calculate_file_sha256(file_path)

        if mime_type is not None:
            self.mime_type = normalize_text(
                mime_type,
                field_name="evidence.mime_type",
            )

        self.verification_level = VerificationLevel.HASH_CONFIRMED
        self.status = EvidenceStatus.PROCESSING
        self.identity.touch()

    def verify_local_file(self) -> bool:
        """Bağlı dosyanın güncel SHA-256 değerini doğrular."""

        if self.local_path is None:
            raise EvidenceIntegrityError(
                "Kanıta bağlı yerel dosya bulunmuyor."
            )

        if self.sha256_digest is None:
            raise EvidenceIntegrityError(
                "Kanıtın kayıtlı SHA-256 değeri bulunmuyor."
            )

        current_digest = calculate_file_sha256(self.local_path)
        verified = current_digest == self.sha256_digest

        if verified:
            self.status = EvidenceStatus.VERIFIED
            self.verification_level = (
                VerificationLevel.DIGITALLY_VERIFIED
            )
            self.verified_at = utc_now()
        else:
            self.status = EvidenceStatus.REVIEW_REQUIRED
            self.metadata["integrity_failure_at"] = utc_now()
            self.metadata["expected_sha256"] = self.sha256_digest
            self.metadata["actual_sha256"] = current_digest

        self.identity.touch()

        return verified

    def reject(self, reason: str) -> None:
        """Kanıtı gerekçesiyle reddeder."""

        self.status = EvidenceStatus.REJECTED
        self.verification_level = VerificationLevel.UNVERIFIED
        self.metadata["rejection_reason"] = normalize_text(
            reason,
            field_name="evidence.rejection_reason",
        )
        self.metadata["rejected_at"] = utc_now()
        self.identity.touch()

    def to_dict(self) -> dict[str, Any]:
        """Kanıtı JSON uyumlu sözlüğe dönüştürür."""

        return json_safe(
            {
                "identity": self.identity.to_dict(),
                "title": self.title,
                "kind": self.kind,
                "status": self.status,
                "verification_level": self.verification_level,
                "source_uri": self.source_uri,
                "local_path": self.local_path,
                "mime_type": self.mime_type,
                "size_bytes": self.size_bytes,
                "sha256": self.sha256_digest,
                "hash_algorithm": HASH_ALGORITHM,
                "collected_at": self.collected_at,
                "verified_at": self.verified_at,
                "collector_id": self.collector_id,
                "description": self.description,
                "metadata": self.metadata,
            }
        )
