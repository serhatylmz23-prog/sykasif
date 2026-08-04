"""Kanonik JSON ve SHA-256 yardımcıları."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from .utils import json_safe


def canonical_json_bytes(
    payload: Any,
) -> bytes:
    """Veriyi kararlı ve imzalanabilir JSON baytlarına dönüştürür."""

    normalized = json_safe(payload)

    text = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    return text.encode("utf-8")


def calculate_payload_sha256(
    payload: Any,
) -> str:
    """JSON uyumlu verinin SHA-256 değerini üretir."""

    return sha256(canonical_json_bytes(payload)).hexdigest()


def calculate_path_sha256(
    path: str | Path,
    *,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Dosyanın SHA-256 değerini hesaplar."""

    file_path = Path(path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Dosya bulunamadı: {file_path}"
        )

    digest = sha256()

    with file_path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()
