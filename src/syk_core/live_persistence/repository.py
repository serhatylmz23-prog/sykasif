"""Canlı analiz kalıcı JSON deposu."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from ..integrity import calculate_payload_sha256
from ..live_analysis import LiveAnalysisSession
from .audit_chain import LiveAuditChain
from .manifest import LiveAnalysisManifest
from .snapshot import (
    LiveSessionSnapshot,
    restore_live_session,
)


class LiveAnalysisNotFoundError(KeyError):
    """Canlı analiz oturum kaydı bulunamadı."""


class LiveAnalysisIntegrityError(ValueError):
    """Canlı analiz kayıt bütünlüğü geçersiz."""


class LiveAnalysisRepository:
    """Canlı analiz oturumlarını kalıcı JSON dosyalarında saklar."""

    def __init__(
        self,
        root_directory: str | Path,
    ) -> None:
        self.root_directory = Path(
            root_directory
        )
        self.snapshot_directory = (
            self.root_directory / "snapshots"
        )
        self.audit_directory = (
            self.root_directory / "audit"
        )
        self.manifest_directory = (
            self.root_directory / "manifests"
        )
        self.pin_history_directory = (
            self.root_directory / "pin_history"
        )

        for directory in (
            self.snapshot_directory,
            self.audit_directory,
            self.manifest_directory,
            self.pin_history_directory,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    @staticmethod
    def _safe_name(
        session_id: str,
    ) -> str:
        normalized = session_id.strip()

        if not normalized:
            raise ValueError(
                "Oturum kimliği boş olamaz."
            )

        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789-_"
        )

        if any(
            character not in allowed
            for character in normalized
        ):
            raise ValueError(
                "Oturum kimliği güvenli olmayan karakter içeriyor."
            )

        return normalized

    def _snapshot_path(
        self,
        session_id: str,
    ) -> Path:
        return (
            self.snapshot_directory
            / (
                f"{self._safe_name(session_id)}"
                ".snapshot.json"
            )
        )

    def _audit_path(
        self,
        session_id: str,
    ) -> Path:
        return (
            self.audit_directory
            / (
                f"{self._safe_name(session_id)}"
                ".audit.json"
            )
        )

    def _manifest_path(
        self,
        session_id: str,
    ) -> Path:
        return (
            self.manifest_directory
            / (
                f"{self._safe_name(session_id)}"
                ".manifest.json"
            )
        )

    def _pin_history_path(
        self,
        session_id: str,
    ) -> Path:
        return (
            self.pin_history_directory
            / (
                f"{self._safe_name(session_id)}"
                ".pins.json"
            )
        )

    @staticmethod
    def _atomic_write_json(
        path: Path,
        payload: dict[str, Any],
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(
                handle.name
            )

            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )

            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        temporary_path.replace(path)

    @staticmethod
    def _read_json(
        path: Path,
    ) -> dict[str, Any]:
        if not path.is_file():
            raise LiveAnalysisNotFoundError(
                f"Canlı analiz dosyası bulunamadı: {path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise LiveAnalysisIntegrityError(
                f"Canlı analiz JSON dosyası bozuk: {path}"
            ) from exc

        if not isinstance(payload, dict):
            raise LiveAnalysisIntegrityError(
                "Canlı analiz JSON kökü sözlük değil."
            )

        return payload

    def save_session(
        self,
        session: LiveAnalysisSession,
        *,
        actor: str = "system",
    ) -> LiveAnalysisManifest:
        snapshot = LiveSessionSnapshot.from_session(
            session
        )
        snapshot_payload = snapshot.to_dict()
        snapshot_sha256 = (
            calculate_payload_sha256(
                snapshot_payload
            )
        )

        chain = self.load_audit_chain(
            session.session_id,
            required=False,
        )

        action = (
            "live_session_updated"
            if self._snapshot_path(
                session.session_id
            ).exists()
            else "live_session_created"
        )

        chain.append(
            action=action,
            payload=snapshot_payload,
            actor=actor,
            metadata={
                "processed_frame_count": (
                    snapshot
                    .processed_frame_count
                ),
                "failed_frame_count": (
                    snapshot
                    .failed_frame_count
                ),
                "history_record_count": len(
                    snapshot.history_records
                ),
            },
        )

        manifest = (
            LiveAnalysisManifest
            .from_snapshot(
                snapshot=snapshot,
                snapshot_sha256=(
                    snapshot_sha256
                ),
                audit_last_hash=(
                    chain.last_hash
                ),
            )
        )

        envelope = {
            "format": "syk-live-analysis",
            "format_version": "1.0",
            "session_id": (
                session.session_id
            ),
            "snapshot_sha256": (
                snapshot_sha256
            ),
            "payload": snapshot_payload,
        }

        self._atomic_write_json(
            self._snapshot_path(
                session.session_id
            ),
            envelope,
        )
        self._atomic_write_json(
            self._audit_path(
                session.session_id
            ),
            chain.to_dict(),
        )
        self._atomic_write_json(
            self._manifest_path(
                session.session_id
            ),
            manifest.to_dict(),
        )

        return manifest

    def load_snapshot(
        self,
        session_id: str,
        *,
        verify: bool = True,
    ) -> LiveSessionSnapshot:
        envelope = self._read_json(
            self._snapshot_path(
                session_id
            )
        )

        payload = envelope.get(
            "payload"
        )

        if not isinstance(payload, dict):
            raise LiveAnalysisIntegrityError(
                "Canlı oturum anlık görüntü verisi geçersiz."
            )

        actual_sha256 = (
            calculate_payload_sha256(
                payload
            )
        )
        expected_sha256 = envelope.get(
            "snapshot_sha256"
        )

        if (
            verify
            and actual_sha256
            != expected_sha256
        ):
            raise LiveAnalysisIntegrityError(
                "Canlı oturum anlık görüntü SHA-256 doğrulaması başarısız."
            )

        snapshot = (
            LiveSessionSnapshot
            .from_dict(payload)
        )

        if (
            snapshot.session_id
            != session_id
            or envelope.get("session_id")
            != session_id
        ):
            raise LiveAnalysisIntegrityError(
                "Canlı oturum kimliği kayıt zarfıyla eşleşmiyor."
            )

        if verify:
            self.verify(session_id)

        return snapshot

    def restore_session(
        self,
        session_id: str,
        *,
        queue_capacity: int = 120,
    ) -> LiveAnalysisSession:
        snapshot = self.load_snapshot(
            session_id
        )

        return restore_live_session(
            snapshot,
            queue_capacity=queue_capacity,
        )

    def load_audit_chain(
        self,
        session_id: str,
        *,
        required: bool = True,
    ) -> LiveAuditChain:
        path = self._audit_path(
            session_id
        )

        if not path.is_file():
            if required:
                raise LiveAnalysisNotFoundError(
                    f"Canlı denetim zinciri bulunamadı: {session_id}"
                )

            return LiveAuditChain(
                session_id=session_id
            )

        return LiveAuditChain.from_dict(
            self._read_json(path)
        )

    def load_manifest(
        self,
        session_id: str,
    ) -> LiveAnalysisManifest:
        return (
            LiveAnalysisManifest
            .from_dict(
                self._read_json(
                    self._manifest_path(
                        session_id
                    )
                )
            )
        )

    def save_pin_history(
        self,
        *,
        session_id: str,
        pins: tuple[Any, ...],
    ) -> str:
        pin_payloads = [
            (
                pin.to_runtime_dict()
                if hasattr(
                    pin,
                    "to_runtime_dict",
                )
                else dict(pin)
            )
            for pin in pins
        ]

        payload = {
            "session_id": session_id,
            "pin_count": len(
                pin_payloads
            ),
            "pins": pin_payloads,
        }

        payload_sha256 = (
            calculate_payload_sha256(
                payload
            )
        )

        envelope = {
            "format": "syk-live-pin-history",
            "format_version": "1.0",
            "session_id": session_id,
            "payload_sha256": (
                payload_sha256
            ),
            "payload": payload,
        }

        self._atomic_write_json(
            self._pin_history_path(
                session_id
            ),
            envelope,
        )

        chain = self.load_audit_chain(
            session_id
        )
        chain.append(
            action="pin_history_saved",
            payload=payload,
            metadata={
                "pin_count": len(
                    pin_payloads
                ),
            },
        )

        self._atomic_write_json(
            self._audit_path(
                session_id
            ),
            chain.to_dict(),
        )

        manifest = self.load_manifest(
            session_id
        )
        manifest.audit_last_hash = (
            chain.last_hash
        )
        manifest.manifest_sha256 = (
            manifest.calculate_hash()
        )

        self._atomic_write_json(
            self._manifest_path(
                session_id
            ),
            manifest.to_dict(),
        )

        return payload_sha256

    def load_pin_history(
        self,
        session_id: str,
    ) -> tuple[dict[str, Any], ...]:
        envelope = self._read_json(
            self._pin_history_path(
                session_id
            )
        )

        payload = envelope.get(
            "payload"
        )

        if not isinstance(payload, dict):
            raise LiveAnalysisIntegrityError(
                "Harita pin geçmişi verisi geçersiz."
            )

        actual_sha256 = (
            calculate_payload_sha256(
                payload
            )
        )

        if (
            actual_sha256
            != envelope.get(
                "payload_sha256"
            )
        ):
            raise LiveAnalysisIntegrityError(
                "Harita pin geçmişi SHA-256 doğrulaması başarısız."
            )

        return tuple(
            dict(item)
            for item in (
                payload.get("pins")
                or []
            )
        )

    def verify(
        self,
        session_id: str,
    ) -> bool:
        envelope = self._read_json(
            self._snapshot_path(
                session_id
            )
        )
        chain = self.load_audit_chain(
            session_id
        )
        manifest = self.load_manifest(
            session_id
        )

        payload = envelope.get(
            "payload"
        )

        if not isinstance(payload, dict):
            raise LiveAnalysisIntegrityError(
                "Canlı oturum kayıt verisi geçersiz."
            )

        actual_snapshot_sha256 = (
            calculate_payload_sha256(
                payload
            )
        )

        if (
            actual_snapshot_sha256
            != envelope.get(
                "snapshot_sha256"
            )
        ):
            raise LiveAnalysisIntegrityError(
                "Canlı oturum snapshot SHA-256 değeri eşleşmiyor."
            )

        chain.assert_valid()

        if not manifest.verify():
            raise LiveAnalysisIntegrityError(
                "Canlı analiz manifest bütünlüğü geçersiz."
            )

        if (
            manifest.session_id
            != session_id
        ):
            raise LiveAnalysisIntegrityError(
                "Manifest oturum kimliği eşleşmiyor."
            )

        if (
            manifest.snapshot_sha256
            != actual_snapshot_sha256
        ):
            raise LiveAnalysisIntegrityError(
                "Manifest snapshot SHA-256 değeri eşleşmiyor."
            )

        if (
            manifest.audit_last_hash
            != chain.last_hash
        ):
            raise LiveAnalysisIntegrityError(
                "Manifest denetim zinciri son hash değeri eşleşmiyor."
            )

        return True

    def list_session_ids(
        self,
    ) -> tuple[str, ...]:
        suffix = ".snapshot.json"
        identifiers: list[str] = []

        for path in (
            self.snapshot_directory
            .glob(f"*{suffix}")
        ):
            name = path.name

            if name.endswith(suffix):
                identifiers.append(
                    name[:-len(suffix)]
                )

        return tuple(
            sorted(identifiers)
        )

    def delete_session(
        self,
        session_id: str,
    ) -> None:
        snapshot_path = (
            self._snapshot_path(
                session_id
            )
        )

        if not snapshot_path.is_file():
            raise LiveAnalysisNotFoundError(
                f"Canlı analiz oturumu bulunamadı: {session_id}"
            )

        for path in (
            snapshot_path,
            self._audit_path(
                session_id
            ),
            self._manifest_path(
                session_id
            ),
            self._pin_history_path(
                session_id
            ),
        ):
            if path.exists():
                path.unlink()
