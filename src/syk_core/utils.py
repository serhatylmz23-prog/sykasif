"""Genel serileştirme ve zaman yardımcıları."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


def utc_now() -> datetime:
    """Saat dilimi bilgili UTC zaman üretir."""

    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Zaman değerini UTC ve saat dilimi bilgili hale getirir."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def isoformat_utc(value: datetime) -> str:
    """UTC zamanı ISO-8601 metnine dönüştürür."""

    normalized = ensure_utc(value)
    return normalized.isoformat().replace("+00:00", "Z")


def normalize_text(value: str, *, field_name: str) -> str:
    """Boş olmayan kırpılmış metin döndürür."""

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} boş olamaz.")

    return normalized


def json_safe(value: Any) -> Any:
    """Nesneyi JSON ile serileştirilebilir yapıya dönüştürür."""

    if is_dataclass(value):
        return json_safe(asdict(value))

    if isinstance(value, datetime):
        return isoformat_utc(value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_safe(item) for item in value]

    return value
