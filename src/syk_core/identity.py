"""SyKaşif kimlik üretimi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from .constants import SCHEMA_VERSION, SYK_IDENTIFIER_PREFIX
from .utils import isoformat_utc, normalize_text, utc_now


def create_syk_identifier(
    entity_prefix: str,
    *,
    sequence: int | None = None,
    uuid_value: UUID | None = None,
) -> str:
    """Okunabilir ve benzersiz SyKaşif varlık kimliği üretir."""

    prefix = normalize_text(
        entity_prefix,
        field_name="entity_prefix",
    ).upper()

    if not prefix.replace("_", "").isalnum():
        raise ValueError(
            "entity_prefix yalnız harf, rakam ve alt çizgi içerebilir."
        )

    actual_uuid = uuid_value or uuid4()

    if sequence is not None:
        if sequence < 1:
            raise ValueError("sequence en az 1 olmalıdır.")

        return (
            f"{SYK_IDENTIFIER_PREFIX}-"
            f"{prefix}-"
            f"{sequence:07d}-"
            f"{actual_uuid.hex[:8].upper()}"
        )

    return (
        f"{SYK_IDENTIFIER_PREFIX}-"
        f"{prefix}-"
        f"{actual_uuid.hex[:12].upper()}"
    )


@dataclass(slots=True)
class EntityIdentity:
    """Her çekirdek varlığında bulunan ortak kimlik."""

    entity_prefix: str
    syk_id: str | None = None
    uuid: UUID = field(default_factory=uuid4)
    schema_version: str = SCHEMA_VERSION
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.entity_prefix = normalize_text(
            self.entity_prefix,
            field_name="entity_prefix",
        ).upper()

        if self.syk_id is None:
            self.syk_id = create_syk_identifier(
                self.entity_prefix,
                uuid_value=self.uuid,
            )

        self.syk_id = normalize_text(
            self.syk_id,
            field_name="syk_id",
        )

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at, created_at değerinden önce olamaz."
            )

    def touch(self) -> None:
        """Güncelleme zamanını yeniler."""

        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, str]:
        """Kimliği JSON uyumlu sözlüğe dönüştürür."""

        return {
            "syk_id": self.syk_id or "",
            "uuid": str(self.uuid),
            "entity_prefix": self.entity_prefix,
            "schema_version": self.schema_version,
            "created_at": isoformat_utc(self.created_at),
            "updated_at": isoformat_utc(self.updated_at),
        }
