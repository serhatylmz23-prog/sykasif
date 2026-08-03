from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from .scientific_device_evidence import DeviceEvidenceStore


class DeviceEvidencePackageBuilder:
    def __init__(
        self,
        *,
        evidence: DeviceEvidenceStore,
        root: Path | None = None,
    ) -> None:
        self._evidence = evidence
        self._root = (
            root
            or Path("artifacts")
            / "device_session_packages"
        )
        self._lock = RLock()

        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def root(self) -> Path:
        return self._root

    def package_directory(
        self,
        session_id: str,
    ) -> Path:
        safe_id = self._safe_id(session_id)
        return self._root / safe_id

    def package_path(
        self,
        session_id: str,
    ) -> Path:
        safe_id = self._safe_id(session_id)
        return self._root / f"{safe_id}.zip"

    def build(
        self,
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        session_id = str(session["id"])

        with self._lock:
            evidence_verification = (
                self._evidence.verify(session_id)
            )

            if not evidence_verification["valid"]:
                raise ValueError(
                    "Kanıt zinciri doğrulanamadı."
                )

            records = self._evidence.records(
                session_id
            )

            package_directory = (
                self.package_directory(session_id)
            )

            if package_directory.exists():
                shutil.rmtree(package_directory)

            package_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            evidence_source = (
                self._evidence.session_path(
                    session_id
                )
            )

            evidence_target = (
                package_directory
                / "evidence.jsonl"
            )

            if evidence_source.is_file():
                shutil.copy2(
                    evidence_source,
                    evidence_target,
                )
            else:
                evidence_target.write_text(
                    "",
                    encoding="utf-8",
                )

            session_path = (
                package_directory
                / "session.json"
            )

            session_path.write_text(
                json.dumps(
                    session,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                ),
                encoding="utf-8",
            )

            manifest = {
                "schema": (
                    "sykasif-device-evidence-"
                    "package/v1"
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
                "sample_count": session.get(
                    "sample_count",
                    0,
                ),
                "evidence_record_count": len(
                    records
                ),
                "evidence_chain_valid": (
                    evidence_verification["valid"]
                ),
                "evidence_last_hash": (
                    evidence_verification.get(
                        "last_hash"
                    )
                ),
                "created_at": datetime.now(
                    UTC
                ).isoformat(),
                "files": [],
            }

            manifest_path = (
                package_directory
                / "manifest.json"
            )

            sha_path = (
                package_directory
                / "sha256sum.txt"
            )

            package_files = [
                evidence_target,
                session_path,
            ]

            sha_lines = []

            for path in package_files:
                digest = self._sha256(path)

                manifest["files"].append(
                    {
                        "name": path.name,
                        "size": path.stat().st_size,
                        "sha256": digest,
                    }
                )

                sha_lines.append(
                    f"{digest}  {path.name}"
                )

            manifest_path.write_text(
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                ),
                encoding="utf-8",
            )

            manifest_hash = self._sha256(
                manifest_path
            )

            sha_lines.append(
                f"{manifest_hash}  "
                f"{manifest_path.name}"
            )

            sha_path.write_text(
                "\n".join(sha_lines) + "\n",
                encoding="utf-8",
            )

            zip_path = self.package_path(
                session_id
            )

            if zip_path.exists():
                zip_path.unlink()

            with zipfile.ZipFile(
                zip_path,
                mode="w",
                compression=(
                    zipfile.ZIP_DEFLATED
                ),
            ) as archive:
                for path in (
                    evidence_target,
                    session_path,
                    manifest_path,
                    sha_path,
                ):
                    archive.write(
                        path,
                        arcname=path.name,
                    )

            return {
                "session_id": session_id,
                "package_path": str(zip_path),
                "package_size": (
                    zip_path.stat().st_size
                ),
                "package_sha256": self._sha256(
                    zip_path
                ),
                "manifest": manifest,
                "verification": (
                    self.verify(session_id)
                ),
            }

    def verify(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        zip_path = self.package_path(
            session_id
        )

        if not zip_path.is_file():
            return {
                "valid": False,
                "reason": "package_not_found",
            }

        with zipfile.ZipFile(
            zip_path,
            mode="r",
        ) as archive:
            names = set(archive.namelist())

            required = {
                "evidence.jsonl",
                "session.json",
                "manifest.json",
                "sha256sum.txt",
            }

            if not required.issubset(names):
                return {
                    "valid": False,
                    "reason": "required_file_missing",
                }

            manifest = json.loads(
                archive.read(
                    "manifest.json"
                ).decode("utf-8")
            )

            for file_info in manifest["files"]:
                name = file_info["name"]
                content = archive.read(name)

                actual_hash = hashlib.sha256(
                    content
                ).hexdigest()

                if (
                    actual_hash
                    != file_info["sha256"]
                ):
                    return {
                        "valid": False,
                        "reason": "sha256_mismatch",
                        "file": name,
                    }

            evidence_lines = [
                line
                for line in archive.read(
                    "evidence.jsonl"
                )
                .decode("utf-8")
                .splitlines()
                if line.strip()
            ]

            if (
                len(evidence_lines)
                != manifest[
                    "evidence_record_count"
                ]
            ):
                return {
                    "valid": False,
                    "reason": (
                        "evidence_count_mismatch"
                    ),
                }

        return {
            "valid": True,
            "session_id": session_id,
            "package_path": str(zip_path),
            "package_sha256": self._sha256(
                zip_path
            ),
            "record_count": manifest[
                "evidence_record_count"
            ],
        }

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