from __future__ import annotations

from .frame_models import (
    FrameIngestionResult,
    FramePacket,
    FrameStatus,
)
from .frame_registry import FrameRegistry
from .frame_service import FrameService


class FrameIngestionEngine:
    def __init__(
        self,
        *,
        registry: FrameRegistry | None = None,
    ) -> None:
        self.registry = (
            registry
            if registry is not None
            else FrameRegistry()
        )

        self.service = FrameService(
            registry=self.registry
        )

    def ingest(
        self,
        packet: FramePacket,
        *,
        status: FrameStatus | str = (
            FrameStatus.CANDIDATE
        ),
    ) -> FrameIngestionResult:
        return self.service.ingest(
            packet,
            status=status,
        )

    def snapshot(self) -> dict:
        records = self.registry.list()

        return {
            "schema": (
                "sykasif-frame-ingestion/v1"
            ),
            "record_count": len(records),
            "records": [
                record.as_dict()
                for record in records
            ],
            "analysis_scope": (
                "digital_frame_candidates"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }