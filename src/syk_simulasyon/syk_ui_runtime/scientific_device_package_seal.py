from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from .scientific_device_evidence_package import (
    DeviceEvidencePackageBuilder,
)


class DeviceEvidencePackageSeal:
    def __init__(
        self,
        *,
        packages: DeviceEvidencePackageBuilder,
        root: Path | None = None,
    ) -> None:
        self._packages = packages
        self._root = (
            root
            or Path("artifacts")
            / "device_session_package_seals"
        )
        self._lock = RLock()

        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def root(self) -> Path:
        return self._root

    def seal_path(
        self,
        session_id: str,
    ) -> Path:
        safe_id = self._safe_id(session_id)

        return self._root / (
            f"{safe_id}.seal.json"
        )

    def report_path(
        self,
        session_id: str,
    ) -> Path:
        safe_id = self._safe_id(session_id)

        return self._root / (
            f"{safe_id}.report.json"
        )

    def create(
        self,
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        session_id = str(session["id"])

        with self._lock:
            verification = (
                self._packages.verify(
                    session_id
                )
            )

            if not verification["valid"]:
                raise ValueError(
                    "Kanıt teslim paketi "
                    "doğrulanamadı."
                )

            package_path = (
                self._packages.package_path(
                    session_id
                )
            )

            package_sha256 = self._sha256(
                package_path
            )

            package_manifest = (
                self._read_manifest(
                    package_path
                )
            )

            report = {
                "schema": (
                    "sykasif-device-session-"
                    "report/v1"
                ),
                "session_id": session_id,
                "device_id": session.get(
                    "device_id"
                ),
                "module_id": session.get(
                    "module_id"
                ),
                "session_state": session.get(
                    "state"
                ),
                "started_at": session.get(
                    "started_at"
                ),
                "stopped_at": session.get(
                    "stopped_at"
                ),
                "sample_count": session.get(
                    "sample_count",
                    0,
                ),
                "evidence_record_count": (
                    verification.get(
                        "record_count",
                        0,
                    )
                ),
                "evidence_chain_valid": (
                    package_manifest.get(
                        "evidence_chain_valid",
                        False,
                    )
                ),
                "package_valid": True,
                "package_path": str(
                    package_path
                ),
                "package_size": (
                    package_path.stat().st_size
                ),
                "package_sha256": (
                    package_sha256
                ),
                "generated_at": datetime.now(
                    UTC
                ).isoformat(),
            }

            report_path = self.report_path(
                session_id
            )

            report_path.write_text(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                ),
                encoding="utf-8",
            )

            report_sha256 = self._sha256(
                report_path
            )

            unsigned_seal = {
                "schema": (
                    "sykasif-device-package-"
                    "seal/v1"
                ),
                "session_id": session_id,
                "package_sha256": (
                    package_sha256
                ),
                "report_sha256": (
                    report_sha256
                ),
                "manifest_sha256": (
                    self._manifest_hash(
                        package_path
                    )
                ),
                "sealed_at": datetime.now(
                    UTC
                ).isoformat(),
                "verification_target": (
                    "verified_conditions"
                ),
                "maximum_digital_confidence": (
                    99.9
                ),
            }

            seal_sha256 = self._dict_hash(
                unsigned_seal
            )

            seal = {
                **unsigned_seal,
                "seal_sha256": seal_sha256,
            }

            seal_path = self.seal_path(
                session_id
            )

            seal_path.write_text(
                json.dumps(
                    seal,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                ),
                encoding="utf-8",
            )

            return {
                "session_id": session_id,
                "report_path": str(
                    report_path
                ),
                "report_sha256": (
                    report_sha256
                ),
                "seal_path": str(
                    seal_path
                ),
                "seal_sha256": (
                    seal_sha256
                ),
                "package_sha256": (
                    package_sha256
                ),
                "verification": (
                    self.verify(session_id)
                ),
            }

    def verify(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        package_path = (
            self._packages.package_path(
                session_id
            )
        )

        report_path = self.report_path(
            session_id
        )

        seal_path = self.seal_path(
            session_id
        )

        if not package_path.is_file():
            return {
                "valid": False,
                "reason": "package_not_found",
            }

        if not report_path.is_file():
            return {
                "valid": False,
                "reason": "report_not_found",
            }

        if not seal_path.is_file():
            return {
                "valid": False,
                "reason": "seal_not_found",
            }

        package_verification = (
            self._packages.verify(
                session_id
            )
        )

        if not package_verification["valid"]:
            return {
                "valid": False,
                "reason": (
                    "package_verification_failed"
                ),
            }

        seal = json.loads(
            seal_path.read_text(
                encoding="utf-8"
            )
        )

        expected_seal_hash = seal.get(
            "seal_sha256"
        )

        unsigned_seal = {
            key: value
            for key, value in seal.items()
            if key != "seal_sha256"
        }

        actual_seal_hash = self._dict_hash(
            unsigned_seal
        )

        if (
            expected_seal_hash
            != actual_seal_hash
        ):
            return {
                "valid": False,
                "reason": "seal_sha256_mismatch",
            }

        actual_package_hash = (
            self._sha256(package_path)
        )

        if (
            seal["package_sha256"]
            != actual_package_hash
        ):
            return {
                "valid": False,
                "reason": (
                    "package_sha256_mismatch"
                ),
            }

        actual_report_hash = (
            self._sha256(report_path)
        )

        if (
            seal["report_sha256"]
            != actual_report_hash
        ):
            return {
                "valid": False,
                "reason": (
                    "report_sha256_mismatch"
                ),
            }

        actual_manifest_hash = (
            self._manifest_hash(
                package_path
            )
        )

        if (
            seal["manifest_sha256"]
            != actual_manifest_hash
        ):
            return {
                "valid": False,
                "reason": (
                    "manifest_sha256_mismatch"
                ),
            }

        return {
            "valid": True,
            "session_id": session_id,
            "package_sha256": (
                actual_package_hash
            ),
            "report_sha256": (
                actual_report_hash
            ),
            "manifest_sha256": (
                actual_manifest_hash
            ),
            "seal_sha256": (
                actual_seal_hash
            ),
        }

    def _read_manifest(
        self,
        package_path: Path,
    ) -> dict[str, Any]:
        with zipfile.ZipFile(
            package_path,
            mode="r",
        ) as archive:
            return json.loads(
                archive.read(
                    "manifest.json"
                ).decode("utf-8")
            )

    def _manifest_hash(
        self,
        package_path: Path,
    ) -> str:
        with zipfile.ZipFile(
            package_path,
            mode="r",
        ) as archive:
            content = archive.read(
                "manifest.json"
            )

        return hashlib.sha256(
            content
        ).hexdigest()

    def _dict_hash(
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

    def _sha256(
        self,
        path: Path,
    ) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as stream:
            while block := stream.read(
                1024 * 1024
            ):
                digest.update(block)

        return digest.hexdigest()

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
                "Geçerli oturum kimliği gerekli."
            )

        return safe