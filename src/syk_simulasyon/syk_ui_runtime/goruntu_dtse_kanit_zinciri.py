from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from syk_core.goruntu.goruntu_kanit_baglanti import (
    GoruntuKaniti,
    GoruntuKanitYoneticisi,
)


class GoruntuDTSEKanitZinciri:
    def __init__(
        self,
        *,
        kanit_yoneticisi: GoruntuKanitYoneticisi,
        root: Path | None = None,
    ) -> None:
        self._kanit_yoneticisi = kanit_yoneticisi
        self._root = (
            root
            or Path("artifacts")
            / "goruntu_dtse_kanit_zinciri"
        )
        self._lock = RLock()

        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def root(self) -> Path:
        return self._root

    def chain_path(
        self,
        media_id: str,
    ) -> Path:
        return self._root / (
            f"{self._safe_id(media_id)}.jsonl"
        )

    def manifest_path(
        self,
        media_id: str,
    ) -> Path:
        return self._root / (
            f"{self._safe_id(media_id)}.manifest.json"
        )

    def append_event(
        self,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_event(event)

        media_id = str(event["media_id"])
        records = self.records(media_id)

        previous_hash = (
            records[-1]["record_sha256"]
            if records
            else None
        )

        unsigned_record = {
            "schema": (
                "sykasif-goruntu-dtse-"
                "evidence-record/v1"
            ),
            "sequence": len(records) + 1,
            "media_id": media_id,
            "dtse_event_id": event["id"],
            "dtse_event_sha256": (
                event["event_sha256"]
            ),
            "source_kind": event["source_kind"],
            "frame_index": event["frame_index"],
            "timestamp_ms": event["timestamp_ms"],
            "signal": event["signal"],
            "syframe": event["syframe"],
            "visual_layer": event["visual_layer"],
            "analysis": event["analysis"],
            "previous_hash": previous_hash,
            "created_at": datetime.now(
                UTC
            ).isoformat(),
        }

        record = {
            **unsigned_record,
            "record_sha256": self._hash(
                unsigned_record
            ),
        }

        with self._lock:
            self._ensure_image_evidence(event)

            with self.chain_path(media_id).open(
                "a",
                encoding="utf-8",
                newline="\n",
            ) as stream:
                stream.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
                stream.write("\n")

            evidence_id = (
                f"DTSE-{event['id']}-"
                f"{record['record_sha256'][:12]}"
            )

            self._kanit_yoneticisi.kanit_bagla(
                media_id,
                evidence_id,
            )

            self._apply_candidate(
                media_id=media_id,
                event=event,
            )

            manifest = self._write_manifest(
                media_id
            )

        return {
            "media_id": media_id,
            "evidence_id": evidence_id,
            "dtse_event_id": event["id"],
            "dtse_event_sha256": (
                event["event_sha256"]
            ),
            "record_sha256": (
                record["record_sha256"]
            ),
            "previous_hash": previous_hash,
            "manifest_sha256": (
                manifest["manifest_sha256"]
            ),
            "chain_valid": self.verify(
                media_id
            )["valid"],
        }

    def records(
        self,
        media_id: str,
    ) -> list[dict[str, Any]]:
        path = self.chain_path(media_id)

        if not path.is_file():
            return []

        return [
            json.loads(line)
            for line in path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

    def manifest(
        self,
        media_id: str,
    ) -> dict[str, Any]:
        path = self.manifest_path(media_id)

        if not path.is_file():
            raise KeyError(media_id)

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    def verify(
        self,
        media_id: str,
    ) -> dict[str, Any]:
        records = self.records(media_id)

        if not records:
            return {
                "valid": False,
                "media_id": media_id,
                "reason": "evidence_chain_not_found",
            }

        previous_hash = None

        for expected_sequence, record in enumerate(
            records,
            start=1,
        ):
            if (
                record.get("sequence")
                != expected_sequence
            ):
                return {
                    "valid": False,
                    "reason": "sequence_mismatch",
                    "failed_sequence": (
                        expected_sequence
                    ),
                }

            if (
                record.get("previous_hash")
                != previous_hash
            ):
                return {
                    "valid": False,
                    "reason": (
                        "previous_hash_mismatch"
                    ),
                    "failed_sequence": (
                        expected_sequence
                    ),
                }

            expected_hash = record.get(
                "record_sha256"
            )

            unsigned = {
                key: value
                for key, value in record.items()
                if key != "record_sha256"
            }

            actual_hash = self._hash(unsigned)

            if expected_hash != actual_hash:
                return {
                    "valid": False,
                    "reason": (
                        "record_sha256_mismatch"
                    ),
                    "failed_sequence": (
                        expected_sequence
                    ),
                }

            previous_hash = actual_hash

        try:
            manifest = self.manifest(media_id)
        except KeyError:
            return {
                "valid": False,
                "reason": "manifest_not_found",
            }

        expected_manifest_hash = (
            manifest.get("manifest_sha256")
        )

        unsigned_manifest = {
            key: value
            for key, value in manifest.items()
            if key != "manifest_sha256"
        }

        actual_manifest_hash = self._hash(
            unsigned_manifest
        )

        if (
            expected_manifest_hash
            != actual_manifest_hash
        ):
            return {
                "valid": False,
                "reason": (
                    "manifest_sha256_mismatch"
                ),
            }

        if (
            manifest["record_count"]
            != len(records)
        ):
            return {
                "valid": False,
                "reason": (
                    "manifest_record_count_mismatch"
                ),
            }

        if (
            manifest["last_record_sha256"]
            != previous_hash
        ):
            return {
                "valid": False,
                "reason": (
                    "manifest_chain_reference_mismatch"
                ),
            }

        return {
            "valid": True,
            "media_id": media_id,
            "record_count": len(records),
            "last_record_sha256": previous_hash,
            "manifest_sha256": (
                actual_manifest_hash
            ),
        }

    def _write_manifest(
        self,
        media_id: str,
    ) -> dict[str, Any]:
        records = self.records(media_id)

        evidence = (
            self._kanit_yoneticisi.getir(
                media_id
            )
        )

        unsigned = {
            "schema": (
                "sykasif-goruntu-dtse-"
                "evidence-manifest/v1"
            ),
            "media_id": media_id,
            "record_count": len(records),
            "first_record_sha256": (
                records[0]["record_sha256"]
            ),
            "last_record_sha256": (
                records[-1]["record_sha256"]
            ),
            "dtse_event_sha256_values": [
                record["dtse_event_sha256"]
                for record in records
            ],
            "evidence_links": list(
                evidence.kanit_baglantilari
            ),
            "digital_scope": (
                "image_video_live_attention_events"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
            "updated_at": datetime.now(
                UTC
            ).isoformat(),
        }

        manifest = {
            **unsigned,
            "manifest_sha256": self._hash(
                unsigned
            ),
        }

        self.manifest_path(media_id).write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ),
            encoding="utf-8",
        )

        return manifest

    def _ensure_image_evidence(
        self,
        event: dict[str, Any],
    ) -> None:
        media_id = str(event["media_id"])

        if (
            self._kanit_yoneticisi.getir(
                media_id
            )
            is not None
        ):
            return

        descriptions = {
            "image": "DTSE fotoğraf kaydı",
            "video": "DTSE video kaydı",
            "live": "DTSE canlı akış kaydı",
        }

        self._kanit_yoneticisi.kaydet(
            GoruntuKaniti(
                media_id,
                descriptions.get(
                    event["source_kind"],
                    "DTSE görüntü kaydı",
                ),
            )
        )

    def _apply_candidate(
        self,
        *,
        media_id: str,
        event: dict[str, Any],
    ) -> None:
        label = str(
            event["signal"]["label"]
        )
        kind = str(
            event["signal"]["kind"]
        )

        if kind in {
            "object",
            "symbol",
            "geometry",
            "anomaly",
        }:
            self._kanit_yoneticisi.nesne_adayi_ekle(
                media_id,
                label,
            )

        if kind in {
            "surface",
            "texture",
            "thermal",
            "spectral",
        }:
            self._kanit_yoneticisi.materyal_adayi_ekle(
                media_id,
                label,
            )

    def _validate_event(
        self,
        event: dict[str, Any],
    ) -> None:
        required = {
            "id",
            "media_id",
            "source_kind",
            "frame_index",
            "timestamp_ms",
            "signal",
            "syframe",
            "visual_layer",
            "analysis",
            "event_sha256",
        }

        missing = required.difference(event)

        if missing:
            raise ValueError(
                "DTSE olayında eksik alanlar: "
                + ", ".join(sorted(missing))
            )

        unsigned = {
            key: value
            for key, value in event.items()
            if key != "event_sha256"
        }

        if (
            event["event_sha256"]
            != self._hash(unsigned)
        ):
            raise ValueError(
                "DTSE olay SHA-256 "
                "doğrulaması başarısız."
            )

    def _hash(
        self,
        payload: dict[str, Any],
    ) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(
            canonical
        ).hexdigest()

    def _safe_id(
        self,
        value: str,
    ) -> str:
        safe = "".join(
            character
            for character in value
            if character.isalnum()
            or character in {"-", "_"}
        )

        if not safe:
            raise ValueError(
                "Geçerli görüntü kimliği gerekli."
            )

        return safe