"""Canlı analiz verisini akıllı rapor motoruna aktarır."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..integrity import calculate_payload_sha256
from ..live_analysis import LiveAnalysisSession
from ..utils import json_safe, utc_now
from .manifest import LiveAnalysisManifest
from .snapshot import LiveSessionSnapshot


@dataclass(slots=True)
class LiveReportPayload:
    """Akıllı rapor motorunun kullanacağı canlı analiz verisi."""

    session_id: str
    title: str
    section_code: str
    summary: dict[str, Any]
    map_blocks: tuple[
        dict[str, Any],
        ...,
    ]
    evidence_blocks: tuple[
        dict[str, Any],
        ...,
    ]
    detection_blocks: tuple[
        dict[str, Any],
        ...,
    ]
    timeline_blocks: tuple[
        dict[str, Any],
        ...,
    ]
    manifest_reference: dict[str, Any]
    generated_at: Any = field(
        default_factory=utc_now
    )
    payload_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError(
                "Rapor oturum kimliği boş olamaz."
            )

        if not self.title.strip():
            raise ValueError(
                "Rapor başlığı boş olamaz."
            )

        if not self.section_code.strip():
            raise ValueError(
                "Rapor bölüm kodu boş olamaz."
            )

        calculated = self.calculate_hash()

        if self.payload_sha256 is None:
            self.payload_sha256 = calculated
        elif self.payload_sha256 != calculated:
            raise ValueError(
                "Canlı rapor verisi SHA-256 değeri geçersiz."
            )

    def unsigned_payload(self) -> dict[str, Any]:
        return json_safe(
            {
                "session_id": self.session_id,
                "title": self.title,
                "section_code": self.section_code,
                "summary": self.summary,
                "map_blocks": list(
                    self.map_blocks
                ),
                "evidence_blocks": list(
                    self.evidence_blocks
                ),
                "detection_blocks": list(
                    self.detection_blocks
                ),
                "timeline_blocks": list(
                    self.timeline_blocks
                ),
                "manifest_reference": (
                    self.manifest_reference
                ),
                "generated_at": (
                    self.generated_at
                ),
            }
        )

    def calculate_hash(self) -> str:
        return calculate_payload_sha256(
            self.unsigned_payload()
        )

    def verify(self) -> bool:
        return (
            self.payload_sha256
            == self.calculate_hash()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.unsigned_payload(),
            "payload_sha256": (
                self.payload_sha256
            ),
        }


class LiveReportBridge:
    """Canlı analiz oturumundan dinamik rapor blokları üretir."""

    def build(
        self,
        *,
        session: LiveAnalysisSession,
        manifest: LiveAnalysisManifest,
        pins: tuple[
            dict[str, Any],
            ...,
        ] = tuple(),
    ) -> LiveReportPayload:
        snapshot = (
            LiveSessionSnapshot
            .from_session(session)
        )

        history = snapshot.history_records

        fish_records = [
            record
            for record in history
            if str(
                record.get(
                    "entity_type",
                    "",
                )
            ).casefold() == "fish"
        ]

        plant_records = [
            record
            for record in history
            if str(
                record.get(
                    "entity_type",
                    "",
                )
            ).casefold() == "plant"
        ]

        average_confidence = (
            round(
                sum(
                    float(
                        record[
                            "confidence_score"
                        ]
                    )
                    for record in history
                )
                / len(history),
                3,
            )
            if history
            else 0.0
        )

        evidence_ids = sorted(
            {
                evidence_id
                for record in history
                for evidence_id in (
                    record.get(
                        "evidence_ids"
                    )
                    or []
                )
            }
        )

        map_blocks = tuple(
            {
                "block_type": "dynamic_map_pin",
                "pin": pin,
            }
            for pin in pins
        )

        detection_blocks = tuple(
            {
                "block_type": (
                    "live_detection"
                ),
                "record_id": record[
                    "record_id"
                ],
                "entity_type": record[
                    "entity_type"
                ],
                "label": record[
                    "detected_label"
                ],
                "confidence_score": record[
                    "confidence_score"
                ],
                "location": record[
                    "location"
                ],
                "species_id": record.get(
                    "species_id"
                ),
                "state": record[
                    "state"
                ],
            }
            for record in history
        )

        evidence_blocks = tuple(
            {
                "block_type": "evidence_reference",
                "evidence_id": evidence_id,
            }
            for evidence_id in evidence_ids
        )

        timeline_blocks = tuple(
            {
                "block_type": "timeline_event",
                "record_id": record[
                    "record_id"
                ],
                "detected_at": record[
                    "detected_at"
                ],
                "label": record[
                    "detected_label"
                ],
                "entity_type": record[
                    "entity_type"
                ],
            }
            for record in history
        )

        return LiveReportPayload(
            session_id=session.session_id,
            title=(
                "Canlı Kamera ve Ekosistem "
                "Analizi"
            ),
            section_code=(
                "live_ecosystem_analysis"
            ),
            summary={
                "session_state": (
                    session.state.value
                ),
                "processed_frame_count": (
                    session
                    .processed_frame_count
                ),
                "failed_frame_count": (
                    session
                    .failed_frame_count
                ),
                "detection_count": len(
                    history
                ),
                "fish_detection_count": len(
                    fish_records
                ),
                "plant_detection_count": len(
                    plant_records
                ),
                "average_confidence": (
                    average_confidence
                ),
                "map_pin_count": len(pins),
                "dynamic": True,
            },
            map_blocks=map_blocks,
            evidence_blocks=(
                evidence_blocks
            ),
            detection_blocks=(
                detection_blocks
            ),
            timeline_blocks=(
                timeline_blocks
            ),
            manifest_reference={
                "manifest_sha256": (
                    manifest
                    .manifest_sha256
                ),
                "snapshot_sha256": (
                    manifest
                    .snapshot_sha256
                ),
                "audit_last_hash": (
                    manifest
                    .audit_last_hash
                ),
                "entry_count": len(
                    manifest.entries
                ),
            },
        )
