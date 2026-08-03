from __future__ import annotations

from threading import RLock

from .frame_models import (
    FrameIngestionResult,
    FrameRecord,
)


class FrameRegistry:
    def __init__(self) -> None:
        self._records: dict[
            str,
            FrameRecord,
        ] = {}

        self._signatures: dict[
            tuple[str, str],
            str,
        ] = {}

        self._order: list[str] = []
        self._lock = RLock()

    def register(
        self,
        record: FrameRecord,
    ) -> FrameIngestionResult:
        signature = (
            record.media_id,
            record.frame_sha256,
        )

        with self._lock:
            existing_id = (
                self._signatures.get(
                    signature
                )
            )

            if existing_id is not None:
                existing = self._records[
                    existing_id
                ]

                return FrameIngestionResult(
                    record=existing,
                    duplicate=True,
                    duplicate_of=existing_id,
                )

            self._records[
                record.frame_id
            ] = record

            self._signatures[
                signature
            ] = record.frame_id

            self._order.append(
                record.frame_id
            )

            return FrameIngestionResult(
                record=record,
                duplicate=False,
                duplicate_of=None,
            )

    def get(
        self,
        frame_id: str,
    ) -> FrameRecord | None:
        with self._lock:
            return self._records.get(
                frame_id
            )

    def list(
        self,
        *,
        media_id: str | None = None,
    ) -> list[FrameRecord]:
        with self._lock:
            records = [
                self._records[frame_id]
                for frame_id in self._order
            ]

        if media_id is None:
            return records

        return [
            record
            for record in records
            if record.media_id == media_id
        ]

    def count(self) -> int:
        with self._lock:
            return len(self._records)