"""Araştırma noktası değişiklik geçmişi ve SHA zinciri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .integrity import calculate_payload_sha256
from .persistence_errors import HistoryIntegrityError
from .utils import isoformat_utc, json_safe, utc_now


GENESIS_HASH = "0" * 64


@dataclass(slots=True)
class ChangeEvent:
    """SHA zincirine bağlı tek değişiklik olayı."""

    sequence: int
    action: str
    entity_id: str
    payload_hash: str
    previous_hash: str
    actor: str = "system"
    timestamp: datetime = field(default_factory=utc_now)
    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    event_hash: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError(
                "Değişiklik sıra numarası en az 1 olmalıdır."
            )

        self.action = self.action.strip()
        self.entity_id = self.entity_id.strip()
        self.actor = self.actor.strip()

        if not self.action:
            raise ValueError("Değişiklik eylemi boş olamaz.")

        if not self.entity_id:
            raise ValueError("Değişiklik varlık kimliği boş olamaz.")

        if not self.actor:
            raise ValueError("Değişiklik aktörü boş olamaz.")

        for name, digest in (
            ("payload_hash", self.payload_hash),
            ("previous_hash", self.previous_hash),
        ):
            if len(digest) != 64:
                raise ValueError(
                    f"{name} 64 karakter olmalıdır."
                )

            int(digest, 16)

        calculated = self.calculate_hash()

        if self.event_hash is None:
            self.event_hash = calculated
        elif self.event_hash != calculated:
            raise HistoryIntegrityError(
                "Değişiklik olayı hash değeri geçersiz."
            )

    def unsigned_payload(self) -> dict[str, Any]:
        """Event hash hesabına giren alanları döndürür."""

        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "action": self.action,
            "entity_id": self.entity_id,
            "payload_hash": self.payload_hash,
            "previous_hash": self.previous_hash,
            "actor": self.actor,
            "timestamp": isoformat_utc(self.timestamp),
            "metadata": json_safe(self.metadata),
        }

    def calculate_hash(self) -> str:
        """Olayın SHA-256 değerini hesaplar."""

        return calculate_payload_sha256(
            self.unsigned_payload()
        )

    def verify(self) -> bool:
        """Olayın kendi bütünlüğünü doğrular."""

        return self.event_hash == self.calculate_hash()

    def to_dict(self) -> dict[str, Any]:
        """Olayı JSON uyumlu sözlüğe dönüştürür."""

        return {
            **self.unsigned_payload(),
            "event_hash": self.event_hash,
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ChangeEvent":
        """Sözlükten değişiklik olayı oluşturur."""

        from .deserialization import parse_datetime

        timestamp = parse_datetime(payload.get("timestamp"))

        if timestamp is None:
            raise HistoryIntegrityError(
                "Değişiklik zamanı bulunamadı."
            )

        return cls(
            event_id=str(payload["event_id"]),
            sequence=int(payload["sequence"]),
            action=str(payload["action"]),
            entity_id=str(payload["entity_id"]),
            payload_hash=str(payload["payload_hash"]),
            previous_hash=str(payload["previous_hash"]),
            actor=str(payload.get("actor", "system")),
            timestamp=timestamp,
            metadata=dict(payload.get("metadata") or {}),
            event_hash=str(payload["event_hash"]),
        )


@dataclass(slots=True)
class ChangeHistory:
    """Araştırma noktası değişiklik olaylarını zincir halinde tutar."""

    entity_id: str
    events: list[ChangeEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.entity_id = self.entity_id.strip()

        if not self.entity_id:
            raise ValueError(
                "Geçmiş varlık kimliği boş olamaz."
            )

    @property
    def last_hash(self) -> str:
        """Zincirin son hash değerini döndürür."""

        if not self.events:
            return GENESIS_HASH

        return self.events[-1].event_hash or GENESIS_HASH

    def append(
        self,
        *,
        action: str,
        payload: Any,
        actor: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> ChangeEvent:
        """Yeni değişiklik olayını zincire ekler."""

        event = ChangeEvent(
            sequence=len(self.events) + 1,
            action=action,
            entity_id=self.entity_id,
            payload_hash=calculate_payload_sha256(payload),
            previous_hash=self.last_hash,
            actor=actor,
            metadata=dict(metadata or {}),
        )

        self.events.append(event)

        return event

    def verify(self) -> bool:
        """Tüm SHA zincirini doğrular."""

        expected_previous = GENESIS_HASH

        for expected_sequence, event in enumerate(
            self.events,
            start=1,
        ):
            if event.sequence != expected_sequence:
                return False

            if event.entity_id != self.entity_id:
                return False

            if event.previous_hash != expected_previous:
                return False

            if not event.verify():
                return False

            expected_previous = (
                event.event_hash or GENESIS_HASH
            )

        return True

    def assert_valid(self) -> None:
        """Zincir bozuksa istisna üretir."""

        if not self.verify():
            raise HistoryIntegrityError(
                "Değişiklik geçmişi SHA zinciri geçersiz."
            )

    def to_dict(self) -> dict[str, Any]:
        """Geçmişi JSON uyumlu sözlüğe dönüştürür."""

        return {
            "entity_id": self.entity_id,
            "event_count": len(self.events),
            "last_hash": self.last_hash,
            "events": [
                event.to_dict()
                for event in self.events
            ],
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ChangeHistory":
        """Sözlükten değişiklik geçmişi oluşturur."""

        history = cls(
            entity_id=str(payload["entity_id"]),
            events=[
                ChangeEvent.from_dict(item)
                for item in payload.get("events") or []
            ],
        )

        history.assert_valid()

        return history
