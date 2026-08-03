from __future__ import annotations

from datetime import UTC, datetime

from .frame_hash import FrameHash
from .frame_models import (
    FrameIngestionResult,
    FramePacket,
    FrameRecord,
    FrameStatus,
)
from .frame_registry import FrameRegistry


class FrameService:
    def __init__(
        self,
        registry: FrameRegistry | None = None,
    ) -> None:
        self.registry = (
            registry
            if registry is not None
            else FrameRegistry()
        )

    def ingest(
        self,
        packet: FramePacket,
        *,
        status: FrameStatus | str = (
            FrameStatus.CANDIDATE
        ),
    ) -> FrameIngestionResult:
        try:
            resolved_status = FrameStatus(
                status
            )
        except ValueError as error:
            raise ValueError(
                "Kare durumu candidate "
                "veya preview olmalıdır."
            ) from error

        frame_sha256 = (
            FrameHash.payload_sha256(
                packet.payload
            )
        )

        source_sha256 = (
            packet.source_sha256
            or frame_sha256
        )

        frame_id = FrameHash.frame_id(
            media_id=packet.media_id,
            source_kind=(
                packet.source_kind.value
            ),
            frame_index=packet.frame_index,
            timestamp_ms=packet.timestamp_ms,
            frame_sha256=frame_sha256,
        )

        record = FrameRecord(
            frame_id=frame_id,
            media_id=packet.media_id,
            source_kind=packet.source_kind,
            frame_index=packet.frame_index,
            timestamp_ms=packet.timestamp_ms,
            frame_width=packet.frame_width,
            frame_height=packet.frame_height,
            payload_size=len(
                packet.payload
            ),
            frame_sha256=frame_sha256,
            source_sha256=source_sha256,
            status=resolved_status,
            created_at=datetime.now(
                UTC
            ).isoformat(),
        )

        return self.registry.register(
            record
        )