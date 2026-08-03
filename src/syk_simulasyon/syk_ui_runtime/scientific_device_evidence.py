from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any


class DeviceEvidenceStore:
    def __init__(
        self,
        root: Path | None = None,
    ) -> None:
        self._root = (
            root
            or Path("artifacts")
            / "device_session_evidence"
        )

        self._lock = RLock()
        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def root(self) -> Path:
        return self._root

    def session_path(
        self,
        session_id: str,
    ) -> Path:
        safe_id = "".join(
            character
            for character in session_id
            if character.isalnum()
            or character in {"-", "_"}
        )

        if not safe_id:
            raise ValueError(
                "Geçerli oturum kimliği gerekli."
            )

        return self._root / f"{safe_id}.jsonl"

    def append(
        self,
        *,
        session_id: str,
        device_id: str,
        module_id: str | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        path = self.session_path(session_id)

        with self._lock:
            previous_hash = self._last_hash(path)

            record = {
                "session_id": session_id,
                "device_id": device_id,
                "module_id": module_id,
                "sequence": self.count(session_id) + 1,
                "recorded_at": datetime.now(
                    UTC
                ).isoformat(),
                "payload": payload,
                "previous_hash": previous_hash,
            }

            canonical = json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            record["sha256"] = hashlib.sha256(
                canonical
            ).hexdigest()

            with path.open(
                "a",
                encoding="utf-8",
                newline="\n",
            ) as stream:
                stream.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )
                stream.write("\n")

            return record

    def records(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        path = self.session_path(session_id)

        if not path.is_file():
            return []

        with self._lock:
            return [
                json.loads(line)
                for line in path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

    def count(
        self,
        session_id: str,
    ) -> int:
        return len(
            self.records(session_id)
        )

    def verify(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        records = self.records(session_id)

        previous_hash = None

        for index, record in enumerate(
            records,
            start=1,
        ):
            expected_hash = record["sha256"]

            unsigned = {
                key: value
                for key, value in record.items()
                if key != "sha256"
            }

            canonical = json.dumps(
                unsigned,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            actual_hash = hashlib.sha256(
                canonical
            ).hexdigest()

            if expected_hash != actual_hash:
                return {
                    "valid": False,
                    "record_count": len(records),
                    "failed_sequence": index,
                    "reason": "sha256_mismatch",
                }

            if (
                record["previous_hash"]
                != previous_hash
            ):
                return {
                    "valid": False,
                    "record_count": len(records),
                    "failed_sequence": index,
                    "reason": "chain_mismatch",
                }

            previous_hash = expected_hash

        return {
            "valid": True,
            "record_count": len(records),
            "last_hash": previous_hash,
        }

    def _last_hash(
        self,
        path: Path,
    ) -> str | None:
        if not path.is_file():
            return None

        lines = [
            line
            for line in path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        if not lines:
            return None

        return json.loads(
            lines[-1]
        )["sha256"]