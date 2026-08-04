"""Canlı analiz SHA-256 denetim zinciri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..integrity import calculate_payload_sha256
from ..utils import isoformat_utc, json_safe, utc_now


LIVE_GENESIS_HASH = "0" * 64


@dataclass(slots=True)
class LiveAuditEvent:
    """Canlı analizdeki tek denetim olayı."""

    sequence: int
    session_id: str
    action: str
    payload_sha256: str
    previous_hash: str
    actor: str = "system"
    event_id: str = field(
        default_factory=lambda: (
            f"SYK-LAUD-{uuid4().hex[:16].upper()}"
        )
    )
    created_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_sha256: str | None = None

    def __post_init__(self) -> None:
        self.session_id = self.session_id.strip()
        self.action = self.action.strip()
        self.actor = self.actor.strip()

        if self.sequence < 1:
            raise ValueError(
                "Denetim olay sıra numarası en az 1 olmalıdır."
            )

        if not self.session_id:
            raise ValueError(
                "Denetim olay oturum kimliği boş olamaz."
            )

        if not self.action:
            raise ValueError(
                "Denetim olay eylemi boş olamaz."
            )

        if not self.actor:
            raise ValueError(
                "Denetim olay aktörü boş olamaz."
            )

        for name, digest in (
            ("payload_sha256", self.payload_sha256),
            ("previous_hash", self.previous_hash),
        ):
            if len(digest) != 64:
                raise ValueError(
                    f"{name} 64 karakter olmalıdır."
                )

            int(digest, 16)

        calculated = self.calculate_hash()

        if self.event_sha256 is None:
            self.event_sha256 = calculated
        elif self.event_sha256 != calculated:
            raise ValueError(
                "Canlı denetim olayı SHA-256 değeri geçersiz."
            )

    def unsigned_payload(self) -> dict[str, Any]:
        return json_safe(
            {
                "event_id": self.event_id,
                "sequence": self.sequence,
                "session_id": self.session_id,
                "action": self.action,
                "payload_sha256": self.payload_sha256,
                "previous_hash": self.previous_hash,
                "actor": self.actor,
                "created_at": isoformat_utc(
                    self.created_at
                ),
                "metadata": self.metadata,
            }
        )

    def calculate_hash(self) -> str:
        return calculate_payload_sha256(
            self.unsigned_payload()
        )

    def verify(self) -> bool:
        return (
            self.event_sha256
            == self.calculate_hash()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.unsigned_payload(),
            "event_sha256": self.event_sha256,
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "LiveAuditEvent":
        from ..deserialization import parse_datetime

        created_at = parse_datetime(
            payload.get("created_at")
        )

        if created_at is None:
            raise ValueError(
                "Denetim olay zamanı bulunamadı."
            )

        return cls(
            event_id=str(payload["event_id"]),
            sequence=int(payload["sequence"]),
            session_id=str(payload["session_id"]),
            action=str(payload["action"]),
            payload_sha256=str(
                payload["payload_sha256"]
            ),
            previous_hash=str(
                payload["previous_hash"]
            ),
            actor=str(
                payload.get("actor", "system")
            ),
            created_at=created_at,
            metadata=dict(
                payload.get("metadata") or {}
            ),
            event_sha256=str(
                payload["event_sha256"]
            ),
        )


@dataclass(slots=True)
class LiveAuditChain:
    """Canlı analiz olaylarını değiştirilemez sırada tutar."""

    session_id: str
    events: list[LiveAuditEvent] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        self.session_id = self.session_id.strip()

        if not self.session_id:
            raise ValueError(
                "Denetim zinciri oturum kimliği boş olamaz."
            )

    @property
    def last_hash(self) -> str:
        if not self.events:
            return LIVE_GENESIS_HASH

        return (
            self.events[-1].event_sha256
            or LIVE_GENESIS_HASH
        )

    def append(
        self,
        *,
        action: str,
        payload: Any,
        actor: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> LiveAuditEvent:
        event = LiveAuditEvent(
            sequence=len(self.events) + 1,
            session_id=self.session_id,
            action=action,
            payload_sha256=(
                calculate_payload_sha256(payload)
            ),
            previous_hash=self.last_hash,
            actor=actor,
            metadata=dict(metadata or {}),
        )

        self.events.append(event)

        return event

    def verify(self) -> bool:
        previous_hash = LIVE_GENESIS_HASH

        for expected_sequence, event in enumerate(
            self.events,
            start=1,
        ):
            if event.sequence != expected_sequence:
                return False

            if event.session_id != self.session_id:
                return False

            if event.previous_hash != previous_hash:
                return False

            if not event.verify():
                return False

            previous_hash = (
                event.event_sha256
                or LIVE_GENESIS_HASH
            )

        return True

    def assert_valid(self) -> None:
        if not self.verify():
            raise ValueError(
                "Canlı analiz denetim zinciri geçersiz."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
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
    ) -> "LiveAuditChain":
        chain = cls(
            session_id=str(payload["session_id"]),
            events=[
                LiveAuditEvent.from_dict(item)
                for item in (
                    payload.get("events") or []
                )
            ],
        )

        chain.assert_valid()

        return chain
