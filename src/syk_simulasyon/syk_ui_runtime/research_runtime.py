from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from .project_runtime import project_repository


@dataclass(slots=True)
class ResearchRecord:
    research_id: str
    project_id: str
    title: str
    research_type: str
    notes: str
    status: str
    media_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    map_layers: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, ResearchRecord] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    def create(
        self,
        *,
        project_id: str,
        title: str,
        research_type: str,
        notes: str = "",
    ) -> ResearchRecord:
        project = project_repository.get(project_id)

        if project is None:
            raise LookupError("Bağlı proje bulunamadı.")

        clean_title = title.strip()
        clean_type = research_type.strip()

        if not clean_title:
            raise ValueError("Araştırma başlığı boş bırakılamaz.")

        if not clean_type:
            raise ValueError("Araştırma türü boş bırakılamaz.")

        now = self._now()

        record = ResearchRecord(
            research_id=str(uuid4()),
            project_id=project_id,
            title=clean_title,
            research_type=clean_type,
            notes=notes.strip(),
            status="ready",
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._records[record.research_id] = record

        return record

    def list(
        self,
        *,
        project_id: str | None = None,
    ) -> list[ResearchRecord]:
        with self._lock:
            records = list(self._records.values())

        if project_id is not None:
            records = [
                record
                for record in records
                if record.project_id == project_id
            ]

        return sorted(
            records,
            key=lambda item: item.created_at,
        )

    def get(
        self,
        research_id: str,
    ) -> ResearchRecord | None:
        with self._lock:
            return self._records.get(research_id)

    def start(
        self,
        research_id: str,
    ) -> ResearchRecord | None:
        with self._lock:
            record = self._records.get(research_id)

            if record is None:
                return None

            record.status = "active"
            record.updated_at = self._now()

            return record

    def complete(
        self,
        research_id: str,
    ) -> ResearchRecord | None:
        with self._lock:
            record = self._records.get(research_id)

            if record is None:
                return None

            record.status = "completed"
            record.updated_at = self._now()

            return record

    def add_media(
        self,
        research_id: str,
        media_id: str,
    ) -> ResearchRecord | None:
        return self._append_unique(
            research_id,
            "media_ids",
            media_id,
        )

    def add_evidence(
        self,
        research_id: str,
        evidence_id: str,
    ) -> ResearchRecord | None:
        return self._append_unique(
            research_id,
            "evidence_ids",
            evidence_id,
        )

    def add_map_layer(
        self,
        research_id: str,
        layer_key: str,
    ) -> ResearchRecord | None:
        return self._append_unique(
            research_id,
            "map_layers",
            layer_key,
        )

    def _append_unique(
        self,
        research_id: str,
        field_name: str,
        value: str,
    ) -> ResearchRecord | None:
        clean_value = value.strip()

        if not clean_value:
            raise ValueError("Bağlantı değeri boş bırakılamaz.")

        with self._lock:
            record = self._records.get(research_id)

            if record is None:
                return None

            values = getattr(record, field_name)

            if clean_value not in values:
                values.append(clean_value)

            record.updated_at = self._now()

            return record


research_repository = ResearchRepository()