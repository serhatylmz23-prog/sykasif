"""Araştırma noktaları için kalıcı JSON kayıt deposu."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .change_history import ChangeHistory
from .deserialization import research_point_from_dict
from .integrity import calculate_payload_sha256
from .persistence_errors import (
    ManifestIntegrityError,
    RepositoryIntegrityError,
    ResearchPointAlreadyExistsError,
    ResearchPointNotFoundError,
)
from .research_manifest import ResearchManifest
from .research_point import ResearchPoint


class JsonResearchPointRepository:
    """Araştırma noktalarını atomik JSON dosyalarında saklar."""

    def __init__(
        self,
        root_directory: str | Path,
    ) -> None:
        self.root_directory = Path(root_directory)
        self.points_directory = (
            self.root_directory / "research_points"
        )
        self.history_directory = (
            self.root_directory / "history"
        )
        self.manifest_directory = (
            self.root_directory / "manifests"
        )

        for directory in (
            self.points_directory,
            self.history_directory,
            self.manifest_directory,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    @staticmethod
    def _safe_name(entity_id: str) -> str:
        """Kimliği güvenli dosya adına dönüştürür."""

        normalized = entity_id.strip()

        if not normalized:
            raise ValueError(
                "Araştırma noktası kimliği boş olamaz."
            )

        allowed = {
            character
            for character in (
                "abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789-_"
            )
        }

        if any(
            character not in allowed
            for character in normalized
        ):
            raise ValueError(
                "Araştırma noktası kimliği güvenli olmayan karakter içeriyor."
            )

        return normalized

    def _point_path(
        self,
        entity_id: str,
    ) -> Path:
        return (
            self.points_directory
            / f"{self._safe_name(entity_id)}.json"
        )

    def _history_path(
        self,
        entity_id: str,
    ) -> Path:
        return (
            self.history_directory
            / f"{self._safe_name(entity_id)}.history.json"
        )

    def _manifest_path(
        self,
        entity_id: str,
    ) -> Path:
        return (
            self.manifest_directory
            / f"{self._safe_name(entity_id)}.manifest.json"
        )

    @staticmethod
    def _atomic_write_json(
        path: Path,
        payload: dict[str, Any],
    ) -> None:
        """JSON verisini geçici dosya üzerinden atomik kaydeder."""

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
            temporary_path = Path(handle.name)

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
        """JSON dosyasını sözlük olarak okur."""

        if not path.is_file():
            raise FileNotFoundError(
                f"JSON kayıt dosyası bulunamadı: {path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise RepositoryIntegrityError(
                f"JSON kayıt dosyası bozuk: {path}"
            ) from exc

        if not isinstance(payload, dict):
            raise RepositoryIntegrityError(
                f"JSON kök verisi sözlük değil: {path}"
            )

        return payload

    def exists(
        self,
        entity_id: str,
    ) -> bool:
        """Araştırma noktası kaydının varlığını döndürür."""

        return self._point_path(entity_id).is_file()

    def save(
        self,
        point: ResearchPoint,
        *,
        actor: str = "system",
        replace: bool = True,
    ) -> ResearchManifest:
        """Araştırma noktasını, geçmişini ve manifestini kaydeder."""

        entity_id = point.identity.syk_id or ""

        if not entity_id:
            raise ValueError(
                "Araştırma noktası kimliği boş."
            )

        point_path = self._point_path(entity_id)

        if point_path.exists() and not replace:
            raise ResearchPointAlreadyExistsError(
                f"Araştırma noktası zaten kayıtlı: {entity_id}"
            )

        point_payload = point.to_dict()
        snapshot_sha256 = calculate_payload_sha256(
            point_payload
        )

        history = self.load_history(
            entity_id,
            required=False,
        )

        action = (
            "research_point_updated"
            if point_path.exists()
            else "research_point_created"
        )

        history.append(
            action=action,
            payload=point_payload,
            actor=actor,
            metadata={
                "snapshot_sha256": snapshot_sha256,
                "layer_count": len(point.layers),
                "evidence_count": len(point.evidence),
            },
        )

        manifest = ResearchManifest.from_point(
            point,
            snapshot_sha256=snapshot_sha256,
            history_last_hash=history.last_hash,
        )

        envelope = {
            "format": "syk-research-point",
            "format_version": "1.0",
            "entity_id": entity_id,
            "snapshot_sha256": snapshot_sha256,
            "payload": point_payload,
        }

        self._atomic_write_json(
            point_path,
            envelope,
        )
        self._atomic_write_json(
            self._history_path(entity_id),
            history.to_dict(),
        )
        self._atomic_write_json(
            self._manifest_path(entity_id),
            manifest.to_dict(),
        )

        return manifest

    def load(
        self,
        entity_id: str,
        *,
        verify: bool = True,
    ) -> ResearchPoint:
        """Araştırma noktasını diskten yükler."""

        point_path = self._point_path(entity_id)

        if not point_path.is_file():
            raise ResearchPointNotFoundError(
                f"Araştırma noktası bulunamadı: {entity_id}"
            )

        envelope = self._read_json(point_path)

        try:
            payload = envelope["payload"]
            expected_snapshot = envelope[
                "snapshot_sha256"
            ]
        except KeyError as exc:
            raise RepositoryIntegrityError(
                f"Kayıt zarfı alanı eksik: {exc.args[0]}"
            ) from exc

        if not isinstance(payload, dict):
            raise RepositoryIntegrityError(
                "Araştırma noktası payload alanı geçersiz."
            )

        actual_snapshot = calculate_payload_sha256(
            payload
        )

        if verify and actual_snapshot != expected_snapshot:
            raise RepositoryIntegrityError(
                "Araştırma noktası snapshot SHA-256 doğrulaması başarısız."
            )

        point = research_point_from_dict(payload)

        if (
            point.identity.syk_id != entity_id
            or envelope.get("entity_id") != entity_id
        ):
            raise RepositoryIntegrityError(
                "Araştırma noktası kimliği kayıt zarfıyla eşleşmiyor."
            )

        if verify:
            self.verify(entity_id)

        return point

    def load_history(
        self,
        entity_id: str,
        *,
        required: bool = True,
    ) -> ChangeHistory:
        """Araştırma noktası değişiklik geçmişini yükler."""

        path = self._history_path(entity_id)

        if not path.is_file():
            if required:
                raise ResearchPointNotFoundError(
                    f"Değişiklik geçmişi bulunamadı: {entity_id}"
                )

            return ChangeHistory(
                entity_id=entity_id
            )

        payload = self._read_json(path)

        return ChangeHistory.from_dict(payload)

    def load_manifest(
        self,
        entity_id: str,
    ) -> ResearchManifest:
        """Araştırma noktası manifestini yükler."""

        path = self._manifest_path(entity_id)

        if not path.is_file():
            raise ResearchPointNotFoundError(
                f"Manifest bulunamadı: {entity_id}"
            )

        payload = self._read_json(path)

        return ResearchManifest.from_dict(payload)

    def verify(
        self,
        entity_id: str,
    ) -> bool:
        """Snapshot, geçmiş ve manifest bütünlüğünü doğrular."""

        envelope = self._read_json(
            self._point_path(entity_id)
        )
        history = self.load_history(entity_id)
        manifest = self.load_manifest(entity_id)

        payload = envelope.get("payload")

        if not isinstance(payload, dict):
            raise RepositoryIntegrityError(
                "Snapshot payload verisi geçersiz."
            )

        actual_snapshot = calculate_payload_sha256(
            payload
        )
        expected_snapshot = envelope.get(
            "snapshot_sha256"
        )

        if actual_snapshot != expected_snapshot:
            raise RepositoryIntegrityError(
                "Snapshot SHA-256 değeri eşleşmiyor."
            )

        history.assert_valid()
        manifest.assert_valid()

        if manifest.entity_id != entity_id:
            raise ManifestIntegrityError(
                "Manifest varlık kimliği eşleşmiyor."
            )

        if manifest.snapshot_sha256 != actual_snapshot:
            raise ManifestIntegrityError(
                "Manifest snapshot SHA-256 değeri eşleşmiyor."
            )

        if manifest.history_last_hash != history.last_hash:
            raise ManifestIntegrityError(
                "Manifest geçmiş zinciri hash değeri eşleşmiyor."
            )

        return True

    def list_ids(self) -> tuple[str, ...]:
        """Kayıtlı araştırma noktası kimliklerini döndürür."""

        identifiers = [
            path.stem
            for path in self.points_directory.glob(
                "*.json"
            )
            if path.is_file()
        ]

        return tuple(sorted(identifiers))

    def delete(
        self,
        entity_id: str,
    ) -> None:
        """Araştırma noktası, geçmiş ve manifest dosyalarını siler."""

        point_path = self._point_path(entity_id)

        if not point_path.is_file():
            raise ResearchPointNotFoundError(
                f"Araştırma noktası bulunamadı: {entity_id}"
            )

        for path in (
            point_path,
            self._history_path(entity_id),
            self._manifest_path(entity_id),
        ):
            if path.exists():
                path.unlink()
