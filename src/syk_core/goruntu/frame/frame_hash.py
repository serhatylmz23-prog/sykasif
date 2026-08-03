from __future__ import annotations

import hashlib
import json
from typing import Any


class FrameHash:
    @staticmethod
    def payload_sha256(
        payload: bytes,
    ) -> str:
        if not isinstance(payload, bytes):
            raise TypeError(
                "SHA-256 girdisi bytes olmalıdır."
            )

        if not payload:
            raise ValueError(
                "Boş kare için SHA-256 "
                "üretilemez."
            )

        return hashlib.sha256(
            payload
        ).hexdigest()

    @staticmethod
    def canonical_sha256(
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

    @classmethod
    def frame_id(
        cls,
        *,
        media_id: str,
        source_kind: str,
        frame_index: int,
        timestamp_ms: int,
        frame_sha256: str,
    ) -> str:
        digest = cls.canonical_sha256(
            {
                "media_id": media_id,
                "source_kind": source_kind,
                "frame_index": frame_index,
                "timestamp_ms": timestamp_ms,
                "frame_sha256": frame_sha256,
            }
        )

        return f"FRM-{digest[:24]}"