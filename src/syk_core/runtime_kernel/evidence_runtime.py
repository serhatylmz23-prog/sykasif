"""SyKaşif canlı kanıt çalışma motoru."""

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from threading import RLock
from typing import Any
from uuid import uuid4

from .event_bus import RuntimeEvent, RuntimeEventBus
from .sensor_runtime import (
    SensorPacket,
    SensorPacketRecord,
    SensorPacketState,
)
from .session_manager import RuntimeSessionManager


class EvidenceRuntimeError(RuntimeError):
    """Canlı kanıt çalışma motoru hatası."""


class EvidenceState(str, Enum):
    CREATED = "oluşturuldu"
    PENDING_REVIEW = "inceleme_bekliyor"
    APPROVED = "onaylandı"
    REJECTED = "reddedildi"
    QUARANTINED = "karantinaya_alındı"
    SEALED = "mühürlendi"


class EvidenceConfidenceLevel(str, Enum):
    LOW = "düşük"
    MEDIUM = "orta"
    HIGH = "yüksek"
    VERY_HIGH = "çok_yüksek"


@dataclass(slots=True, frozen=True)
class EvidenceSource:
    source_type: str
    source_id: str
    session_id: str | None = None
    sensor_id: str | None = None
    packet_id: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.source_type.strip():
            raise ValueError(
                "Kanıt kaynak türü boş olamaz."
            )

        if not self.source_id.strip():
            raise ValueError(
                "Kanıt kaynak kimliği boş olamaz."
            )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "kaynak_türü": self.source_type,
            "kaynak_kimliği": self.source_id,
            "oturum_kimliği": self.session_id,
            "sensör_kimliği": self.sensor_id,
            "paket_kimliği": self.packet_id,
            "veri": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class EvidenceRevision:
    revision_id: str
    action: str
    actor: str
    occurred_at: datetime
    previous_hash: str | None
    record_hash: str
    details: dict[str, Any] = field(
        default_factory=dict
    )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "sürüm_kimliği": self.revision_id,
            "işlem": self.action,
            "işlemi_yapan": self.actor,
            "zaman": self.occurred_at.isoformat(),
            "önceki_hash": self.previous_hash,
            "kayıt_hash": self.record_hash,
            "ayrıntılar": dict(self.details),
        }


@dataclass(slots=True)
class EvidenceRecord:
    evidence_id: str
    evidence_type: str
    title: str
    content: dict[str, Any]
    source: EvidenceSource
    created_at: datetime
    content_hash: str
    confidence_score: float | None = None
    state: EvidenceState = (
        EvidenceState.CREATED
    )
    human_approval_required: bool = True
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_by: str | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    quarantined_reason: str | None = None
    sealed_at: datetime | None = None
    seal_hash: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    revisions: list[EvidenceRevision] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError(
                "Kanıt kimliği boş olamaz."
            )

        if not self.evidence_type.strip():
            raise ValueError(
                "Kanıt türü boş olamaz."
            )

        if not self.title.strip():
            raise ValueError(
                "Kanıt başlığı boş olamaz."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "Kanıt zamanı saat dilimi içermelidir."
            )

        if (
            self.confidence_score is not None
            and not 0.0
            <= self.confidence_score
            <= 1.0
        ):
            raise ValueError(
                "Güven puanı 0 ile 1 arasında olmalıdır."
            )

    @property
    def confidence_level(
        self,
    ) -> EvidenceConfidenceLevel | None:
        score = self.confidence_score

        if score is None:
            return None

        if score < 0.40:
            return EvidenceConfidenceLevel.LOW

        if score < 0.70:
            return EvidenceConfidenceLevel.MEDIUM

        if score < 0.90:
            return EvidenceConfidenceLevel.HIGH

        return EvidenceConfidenceLevel.VERY_HIGH

    @property
    def is_terminal(self) -> bool:
        return self.state in {
            EvidenceState.REJECTED,
            EvidenceState.SEALED,
        }

    @property
    def is_immutable(self) -> bool:
        return self.state is EvidenceState.SEALED

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "kanıt_kimliği": self.evidence_id,
            "kanıt_türü": self.evidence_type,
            "başlık": self.title,
            "durum": self.state.value,
            "içerik_hash": self.content_hash,
            "güven_puanı": self.confidence_score,
            "güven_seviyesi": (
                self.confidence_level.value
                if self.confidence_level
                else None
            ),
            "insan_onayı_zorunlu": (
                self.human_approval_required
            ),
            "onaylayan": self.approved_by,
            "onay_zamanı": (
                self.approved_at.isoformat()
                if self.approved_at
                else None
            ),
            "reddeden": self.rejected_by,
            "ret_zamanı": (
                self.rejected_at.isoformat()
                if self.rejected_at
                else None
            ),
            "ret_nedeni": self.rejection_reason,
            "karantina_nedeni": (
                self.quarantined_reason
            ),
            "mühür_zamanı": (
                self.sealed_at.isoformat()
                if self.sealed_at
                else None
            ),
            "mühür_hash": self.seal_hash,
            "oluşturulma_zamanı": (
                self.created_at.isoformat()
            ),
            "kaynak": self.source.to_runtime_dict(),
            "içerik": dict(self.content),
            "veri": dict(self.metadata),
            "sürümler": [
                revision.to_runtime_dict()
                for revision in self.revisions
            ],
        }


@dataclass(slots=True, frozen=True)
class EvidenceReportBlock:
    block_id: str
    evidence_id: str
    block_type: str
    title: str
    payload: dict[str, Any]
    created_at: datetime

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "blok_kimliği": self.block_id,
            "kanıt_kimliği": self.evidence_id,
            "blok_türü": self.block_type,
            "başlık": self.title,
            "içerik": dict(self.payload),
            "oluşturulma_zamanı": (
                self.created_at.isoformat()
            ),
        }


class EvidenceRuntime:
    """Canlı veri paketlerini doğrulanabilir kanıta dönüştürür."""

    def __init__(
        self,
        *,
        event_bus: RuntimeEventBus | None = None,
        session_manager: RuntimeSessionManager | None = None,
        clock: Any | None = None,
        automatic_review_threshold: float = 0.70,
        quarantine_threshold: float = 0.30,
    ) -> None:
        if not 0.0 <= automatic_review_threshold <= 1.0:
            raise ValueError(
                "İnceleme eşiği geçersiz."
            )

        if not 0.0 <= quarantine_threshold <= 1.0:
            raise ValueError(
                "Karantina eşiği geçersiz."
            )

        if quarantine_threshold > automatic_review_threshold:
            raise ValueError(
                "Karantina eşiği inceleme eşiğinden "
                "yüksek olamaz."
            )

        self.event_bus = event_bus or RuntimeEventBus()
        self.session_manager = session_manager
        self._clock = clock or (
            lambda: datetime.now(UTC)
        )

        self.automatic_review_threshold = (
            automatic_review_threshold
        )
        self.quarantine_threshold = (
            quarantine_threshold
        )

        self._records: dict[
            str,
            EvidenceRecord,
        ] = {}

        self._hash_index: dict[
            str,
            str,
        ] = {}

        self._report_blocks: list[
            EvidenceReportBlock
        ] = []

        self._lock = RLock()

    def create(
        self,
        *,
        evidence_type: str,
        title: str,
        content: dict[str, Any],
        source: EvidenceSource,
        confidence_score: float | None = None,
        metadata: dict[str, Any] | None = None,
        evidence_id: str | None = None,
        human_approval_required: bool = True,
    ) -> EvidenceRecord:
        canonical_content = self._canonical_payload(
            {
                "evidence_type": evidence_type,
                "title": title,
                "content": content,
                "source": source.to_runtime_dict(),
            }
        )

        content_hash = self._sha256(
            canonical_content
        )

        duplicate_id = self._hash_index.get(
            content_hash
        )

        if duplicate_id is not None:
            raise EvidenceRuntimeError(
                "Aynı içerik daha önce kanıt olarak "
                f"kaydedilmiş: {duplicate_id}"
            )

        generated_id = (
            evidence_id
            or "SYK-EVIDENCE-"
            + uuid4().hex.upper()
        )

        with self._lock:
            if generated_id in self._records:
                raise EvidenceRuntimeError(
                    "Kanıt kimliği zaten kayıtlı: "
                    f"{generated_id}"
                )

        now = self._clock()

        record = EvidenceRecord(
            evidence_id=generated_id,
            evidence_type=evidence_type,
            title=title,
            content=dict(content),
            source=source,
            created_at=now,
            content_hash=content_hash,
            confidence_score=confidence_score,
            human_approval_required=(
                human_approval_required
            ),
            metadata=dict(metadata or {}),
        )

        if (
            confidence_score is not None
            and confidence_score
            < self.quarantine_threshold
        ):
            record.state = (
                EvidenceState.QUARANTINED
            )
            record.quarantined_reason = (
                "Güven puanı karantina eşiğinin altında."
            )

        elif (
            human_approval_required
            or confidence_score is None
            or confidence_score
            < self.automatic_review_threshold
        ):
            record.state = (
                EvidenceState.PENDING_REVIEW
            )

        else:
            record.state = EvidenceState.APPROVED
            record.approved_by = "sistem"
            record.approved_at = now

        self._append_revision(
            record=record,
            action="oluşturma",
            actor="evidence_runtime",
            details={
                "state": record.state.value,
                "content_hash": content_hash,
            },
        )

        with self._lock:
            self._records[generated_id] = record
            self._hash_index[content_hash] = generated_id

        self._link_to_session(record)

        self._publish(
            topic="runtime.evidence.created",
            record=record,
        )

        if record.state is EvidenceState.QUARANTINED:
            self._publish(
                topic="runtime.evidence.quarantined",
                record=record,
                extra={
                    "reason": (
                        record.quarantined_reason
                    ),
                },
            )

        return record

    def create_from_sensor_packet(
        self,
        packet_record: SensorPacketRecord,
        *,
        evidence_type: str | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        packet = packet_record.packet

        if packet_record.state is (
            SensorPacketState.REJECTED
        ):
            raise EvidenceRuntimeError(
                "Reddedilmiş sensör paketi "
                "kanıta dönüştürülemez."
            )

        source = EvidenceSource(
            source_type="sensör_paketi",
            source_id=packet.packet_id,
            session_id=packet.session_id,
            sensor_id=packet.sensor_id,
            packet_id=packet.packet_id,
            metadata={
                "packet_state": (
                    packet_record.state.value
                ),
                "packet_reason": (
                    packet_record.reason
                ),
            },
        )

        combined_metadata = dict(
            packet.metadata
        )
        combined_metadata.update(
            metadata or {}
        )

        record = self.create(
            evidence_id=packet.evidence_id,
            evidence_type=(
                evidence_type or "sensör_verisi"
            ),
            title=(
                title
                or f"{packet.sensor_id} sensör kanıtı"
            ),
            content={
                "payload": dict(packet.payload),
                "byte_count": packet.byte_count,
                "frame_count": packet.frame_count,
                "recorded_at": (
                    packet.recorded_at.isoformat()
                ),
            },
            source=source,
            confidence_score=(
                packet.quality_score
            ),
            metadata=combined_metadata,
            human_approval_required=True,
        )

        if packet_record.state is (
            SensorPacketState.QUARANTINED
        ):
            record.state = EvidenceState.QUARANTINED
            record.quarantined_reason = (
                packet_record.reason
                or "Sensör paketi karantinada."
            )

            self._append_revision(
                record=record,
                action="sensör_karantinası",
                actor="evidence_runtime",
                details={
                    "reason": record.quarantined_reason,
                },
            )

        return record

    def approve(
        self,
        evidence_id: str,
        *,
        actor: str,
    ) -> EvidenceRecord:
        record = self.get(evidence_id)
        self._ensure_mutable(record)

        if record.state is EvidenceState.REJECTED:
            raise EvidenceRuntimeError(
                "Reddedilmiş kanıt onaylanamaz."
            )

        if record.state is EvidenceState.QUARANTINED:
            raise EvidenceRuntimeError(
                "Karantinadaki kanıt doğrudan "
                "onaylanamaz."
            )

        now = self._clock()

        record.state = EvidenceState.APPROVED
        record.approved_by = actor
        record.approved_at = now
        record.rejected_by = None
        record.rejected_at = None
        record.rejection_reason = None

        self._append_revision(
            record=record,
            action="onay",
            actor=actor,
            details={
                "approved_at": now.isoformat(),
            },
        )

        self._publish(
            topic="runtime.evidence.approved",
            record=record,
            extra={"actor": actor},
        )

        return record

    def reject(
        self,
        evidence_id: str,
        *,
        actor: str,
        reason: str,
    ) -> EvidenceRecord:
        record = self.get(evidence_id)
        self._ensure_mutable(record)

        now = self._clock()

        record.state = EvidenceState.REJECTED
        record.rejected_by = actor
        record.rejected_at = now
        record.rejection_reason = reason

        self._append_revision(
            record=record,
            action="ret",
            actor=actor,
            details={
                "reason": reason,
                "rejected_at": now.isoformat(),
            },
        )

        self._publish(
            topic="runtime.evidence.rejected",
            record=record,
            extra={
                "actor": actor,
                "reason": reason,
            },
        )

        return record

    def release_from_quarantine(
        self,
        evidence_id: str,
        *,
        actor: str,
        reason: str,
    ) -> EvidenceRecord:
        record = self.get(evidence_id)
        self._ensure_mutable(record)

        if record.state is not EvidenceState.QUARANTINED:
            raise EvidenceRuntimeError(
                "Kanıt karantinada değil."
            )

        record.state = (
            EvidenceState.PENDING_REVIEW
        )
        record.quarantined_reason = None

        self._append_revision(
            record=record,
            action="karantinadan_çıkarma",
            actor=actor,
            details={"reason": reason},
        )

        self._publish(
            topic=(
                "runtime.evidence."
                "released_from_quarantine"
            ),
            record=record,
            extra={
                "actor": actor,
                "reason": reason,
            },
        )

        return record

    def update_metadata(
        self,
        evidence_id: str,
        *,
        actor: str,
        metadata: dict[str, Any],
    ) -> EvidenceRecord:
        record = self.get(evidence_id)
        self._ensure_mutable(record)

        record.metadata.update(metadata)

        self._append_revision(
            record=record,
            action="veri_güncelleme",
            actor=actor,
            details={
                "updated_keys": sorted(metadata),
            },
        )

        self._publish(
            topic="runtime.evidence.updated",
            record=record,
            extra={"actor": actor},
        )

        return record

    def seal(
        self,
        evidence_id: str,
        *,
        actor: str,
    ) -> EvidenceRecord:
        record = self.get(evidence_id)
        self._ensure_mutable(record)

        if record.state is not EvidenceState.APPROVED:
            raise EvidenceRuntimeError(
                "Yalnız onaylanmış kanıt mühürlenebilir."
            )

        now = self._clock()

        seal_payload = self._canonical_payload(
            {
                "evidence_id": record.evidence_id,
                "content_hash": record.content_hash,
                "state": record.state.value,
                "source": record.source.to_runtime_dict(),
                "approved_by": record.approved_by,
                "approved_at": (
                    record.approved_at.isoformat()
                    if record.approved_at
                    else None
                ),
                "revision_hashes": [
                    item.record_hash
                    for item in record.revisions
                ],
            }
        )

        record.state = EvidenceState.SEALED
        record.sealed_at = now
        record.seal_hash = self._sha256(
            seal_payload
        )

        self._append_revision(
            record=record,
            action="mühürleme",
            actor=actor,
            details={
                "seal_hash": record.seal_hash,
                "sealed_at": now.isoformat(),
            },
        )

        self._publish(
            topic="runtime.evidence.sealed",
            record=record,
            extra={"actor": actor},
        )

        return record

    def verify(
        self,
        evidence_id: str,
    ) -> bool:
        record = self.get(evidence_id)

        canonical_content = self._canonical_payload(
            {
                "evidence_type": record.evidence_type,
                "title": record.title,
                "content": record.content,
                "source": record.source.to_runtime_dict(),
            }
        )

        if self._sha256(
            canonical_content
        ) != record.content_hash:
            return False

        previous_hash: str | None = None

        for revision in record.revisions:
            revision_payload = self._canonical_payload(
                {
                    "revision_id": revision.revision_id,
                    "action": revision.action,
                    "actor": revision.actor,
                    "occurred_at": (
                        revision.occurred_at.isoformat()
                    ),
                    "previous_hash": (
                        revision.previous_hash
                    ),
                    "details": revision.details,
                }
            )

            expected = self._sha256(
                revision_payload
            )

            if revision.record_hash != expected:
                return False

            if revision.previous_hash != previous_hash:
                return False

            previous_hash = revision.record_hash

        return True

    def create_report_block(
        self,
        evidence_id: str,
        *,
        block_type: str = "kanıt",
    ) -> EvidenceReportBlock:
        record = self.get(evidence_id)

        block = EvidenceReportBlock(
            block_id=(
                "SYK-REPORT-BLOCK-"
                + uuid4().hex.upper()
            ),
            evidence_id=evidence_id,
            block_type=block_type,
            title=record.title,
            payload={
                "evidence_id": record.evidence_id,
                "evidence_type": record.evidence_type,
                "state": record.state.value,
                "confidence_score": (
                    record.confidence_score
                ),
                "confidence_level": (
                    record.confidence_level.value
                    if record.confidence_level
                    else None
                ),
                "content_hash": record.content_hash,
                "seal_hash": record.seal_hash,
                "source": (
                    record.source.to_runtime_dict()
                ),
                "content": dict(record.content),
                "metadata": dict(record.metadata),
                "verified": self.verify(evidence_id),
            },
            created_at=self._clock(),
        )

        self._report_blocks.append(block)

        self._publish(
            topic="runtime.evidence.report_block.created",
            record=record,
            extra={
                "block_id": block.block_id,
                "block_type": block_type,
            },
        )

        return block

    def get(
        self,
        evidence_id: str,
    ) -> EvidenceRecord:
        try:
            return self._records[evidence_id]
        except KeyError as exc:
            raise EvidenceRuntimeError(
                f"Kanıt bulunamadı: {evidence_id}"
            ) from exc

    def list_records(
        self,
    ) -> tuple[EvidenceRecord, ...]:
        return tuple(
            self._records[evidence_id]
            for evidence_id in sorted(self._records)
        )

    @property
    def report_blocks(
        self,
    ) -> tuple[EvidenceReportBlock, ...]:
        return tuple(self._report_blocks)

    def snapshot(self) -> dict[str, Any]:
        records = self.list_records()

        return {
            "toplam_kanıt_sayısı": len(records),
            "inceleme_bekleyen_sayısı": sum(
                1
                for record in records
                if record.state
                is EvidenceState.PENDING_REVIEW
            ),
            "onaylanan_kanıt_sayısı": sum(
                1
                for record in records
                if record.state
                is EvidenceState.APPROVED
            ),
            "reddedilen_kanıt_sayısı": sum(
                1
                for record in records
                if record.state
                is EvidenceState.REJECTED
            ),
            "karantina_kanıtı_sayısı": sum(
                1
                for record in records
                if record.state
                is EvidenceState.QUARANTINED
            ),
            "mühürlü_kanıt_sayısı": sum(
                1
                for record in records
                if record.state
                is EvidenceState.SEALED
            ),
            "rapor_bloğu_sayısı": len(
                self._report_blocks
            ),
            "kanıtlar": [
                record.to_runtime_dict()
                for record in records
            ],
            "rapor_blokları": [
                block.to_runtime_dict()
                for block in self._report_blocks
            ],
        }

    def _link_to_session(
        self,
        record: EvidenceRecord,
    ) -> None:
        session_id = record.source.session_id

        if session_id is None:
            return

        if self.session_manager is None:
            raise EvidenceRuntimeError(
                "Oturum kanıt bağlantısı için "
                "Session Manager gereklidir."
            )

        session = self.session_manager.get(
            session_id
        )

        already_linked = any(
            item.evidence_id == record.evidence_id
            for item in session.evidence_links
        )

        if already_linked:
            return

        self.session_manager.link_evidence(
            session_id,
            evidence_id=record.evidence_id,
            evidence_type=record.evidence_type,
            metadata={
                "content_hash": record.content_hash,
                "source_id": record.source.source_id,
            },
        )

    def _append_revision(
        self,
        *,
        record: EvidenceRecord,
        action: str,
        actor: str,
        details: dict[str, Any],
    ) -> EvidenceRevision:
        previous_hash = (
            record.revisions[-1].record_hash
            if record.revisions
            else None
        )

        revision_id = (
            "SYK-EVIDENCE-REV-"
            + uuid4().hex.upper()
        )

        occurred_at = self._clock()

        payload = self._canonical_payload(
            {
                "revision_id": revision_id,
                "action": action,
                "actor": actor,
                "occurred_at": (
                    occurred_at.isoformat()
                ),
                "previous_hash": previous_hash,
                "details": details,
            }
        )

        revision = EvidenceRevision(
            revision_id=revision_id,
            action=action,
            actor=actor,
            occurred_at=occurred_at,
            previous_hash=previous_hash,
            record_hash=self._sha256(payload),
            details=dict(details),
        )

        record.revisions.append(revision)

        return revision

    def _ensure_mutable(
        self,
        record: EvidenceRecord,
    ) -> None:
        if record.is_immutable:
            raise EvidenceRuntimeError(
                "Mühürlü kanıt değiştirilemez."
            )

    def _canonical_payload(
        self,
        payload: dict[str, Any],
    ) -> bytes:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

    def _sha256(
        self,
        payload: bytes,
    ) -> str:
        return hashlib.sha256(
            payload
        ).hexdigest()

    def _publish(
        self,
        *,
        topic: str,
        record: EvidenceRecord,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "evidence_id": record.evidence_id,
            "evidence_type": record.evidence_type,
            "state": record.state.value,
            "content_hash": record.content_hash,
        }

        payload.update(extra or {})

        self.event_bus.publish(
            RuntimeEvent(
                topic=topic,
                source="evidence_runtime",
                payload=payload,
            )
        )
