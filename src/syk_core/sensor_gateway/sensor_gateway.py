from __future__ import annotations

from hashlib import sha256
from json import dumps
from threading import RLock
from typing import Any

from .sensor_model import (
    SensorEnvelope,
    SensorSource,
)


class SensorGateway:
    def __init__(self) -> None:
        self._lock = RLock()
        self._sources: dict[
            str,
            SensorSource,
        ] = {}
        self._envelopes: list[
            SensorEnvelope
        ] = []
        self._sequences: dict[
            str,
            int,
        ] = {}

    def reset(self) -> None:
        with self._lock:
            self._sources.clear()
            self._envelopes.clear()
            self._sequences.clear()

    def register_source(
        self,
        source: SensorSource,
    ) -> SensorSource:
        with self._lock:
            if source.source_id in self._sources:
                raise ValueError(
                    "Sensör kaynağı zaten kayıtlı: "
                    f"{source.source_id}"
                )

            self._sources[
                source.source_id
            ] = source

            self._sequences[
                source.source_id
            ] = 0

        return source

    def replace_source(
        self,
        source: SensorSource,
    ) -> SensorSource:
        with self._lock:
            self._sources[
                source.source_id
            ] = source

            self._sequences.setdefault(
                source.source_id,
                0,
            )

        return source

    def get_source(
        self,
        source_id: str,
    ) -> SensorSource | None:
        with self._lock:
            return self._sources.get(
                source_id
            )

    def list_sources(
        self,
    ) -> tuple[SensorSource, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._sources.values(),
                    key=lambda item: item.source_id,
                )
            )

    def ingest(
        self,
        source_id: str,
        *,
        payload: dict[str, Any],
        research_id: str | None = None,
        workspace_id: str | None = None,
        evidence_status: str = "candidate-unverified",
        confidence: float = 0.0,
    ) -> SensorEnvelope:
        source = self.get_source(
            source_id
        )

        if source is None:
            raise LookupError(
                "Sensör kaynağı bulunamadı."
            )

        with self._lock:
            sequence = (
                self._sequences[source_id]
                + 1
            )

            envelope = SensorEnvelope.create(
                source=source,
                sequence=sequence,
                payload=payload,
                research_id=research_id,
                workspace_id=workspace_id,
                evidence_status=evidence_status,
                confidence=confidence,
            )

            self._sequences[
                source_id
            ] = sequence

            self._envelopes.append(
                envelope
            )

        return envelope

    def list_envelopes(
        self,
        *,
        source_id: str | None = None,
        research_id: str | None = None,
        workspace_id: str | None = None,
    ) -> tuple[SensorEnvelope, ...]:
        with self._lock:
            envelopes = tuple(
                self._envelopes
            )

        if source_id is not None:
            envelopes = tuple(
                item
                for item in envelopes
                if item.source_id == source_id
            )

        if research_id is not None:
            envelopes = tuple(
                item
                for item in envelopes
                if item.research_id == research_id
            )

        if workspace_id is not None:
            envelopes = tuple(
                item
                for item in envelopes
                if item.workspace_id == workspace_id
            )

        return envelopes

    def snapshot(
        self,
    ) -> dict[str, Any]:
        sources = self.list_sources()
        envelopes = self.list_envelopes()

        source_counts: dict[str, int] = {}

        for envelope in envelopes:
            source_counts[
                envelope.source_id
            ] = (
                source_counts.get(
                    envelope.source_id,
                    0,
                )
                + 1
            )

        return {
            "source_count": len(sources),
            "envelope_count": len(envelopes),
            "sources": [
                source.to_dict()
                for source in sources
            ],
            "source_envelope_counts": (
                source_counts
            ),
        }

    def manifest_digest(
        self,
    ) -> str:
        payload = {
            "sources": [
                source.to_dict()
                for source in self.list_sources()
            ],
            "envelopes": [
                envelope.to_dict()
                for envelope in self.list_envelopes()
            ],
        }

        serialized = dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return sha256(
            serialized.encode("utf-8")
        ).hexdigest()


sensor_gateway = SensorGateway()