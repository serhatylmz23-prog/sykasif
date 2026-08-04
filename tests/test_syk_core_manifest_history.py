from __future__ import annotations

import json
from pathlib import Path

import pytest

from syk_core import (
    ChangeHistory,
    HistoryIntegrityError,
    ManifestIntegrityError,
    ResearchManifest,
    calculate_payload_sha256,
)


def test_change_history_chain_is_valid() -> None:
    history = ChangeHistory(
        entity_id="SYK-RP-TEST"
    )

    first = history.append(
        action="created",
        payload={
            "version": 1,
        },
        actor="tester",
    )
    second = history.append(
        action="updated",
        payload={
            "version": 2,
        },
        actor="tester",
    )

    assert history.verify() is True
    assert second.previous_hash == first.event_hash
    assert history.last_hash == second.event_hash


def test_change_history_detects_tampering() -> None:
    history = ChangeHistory(
        entity_id="SYK-RP-TEST"
    )

    history.append(
        action="created",
        payload={
            "value": 1,
        },
    )

    payload = history.to_dict()
    payload["events"][0]["action"] = "tampered"

    with pytest.raises(
        HistoryIntegrityError
    ):
        ChangeHistory.from_dict(payload)


def test_manifest_roundtrip() -> None:
    manifest = ResearchManifest(
        entity_id="SYK-RP-TEST",
        snapshot_sha256=calculate_payload_sha256(
            {
                "snapshot": 1,
            }
        ),
        history_last_hash=calculate_payload_sha256(
            {
                "history": 1,
            }
        ),
        entries=tuple(),
    )

    restored = ResearchManifest.from_dict(
        manifest.to_dict()
    )

    assert restored.verify() is True
    assert (
        restored.manifest_sha256
        == manifest.manifest_sha256
    )


def test_manifest_detects_tampering() -> None:
    manifest = ResearchManifest(
        entity_id="SYK-RP-TEST",
        snapshot_sha256=calculate_payload_sha256(
            {
                "snapshot": 1,
            }
        ),
        history_last_hash=calculate_payload_sha256(
            {
                "history": 1,
            }
        ),
        entries=tuple(),
    )

    payload = manifest.to_dict()
    payload["entity_id"] = "SYK-RP-TAMPERED"

    with pytest.raises(
        ManifestIntegrityError
    ):
        ResearchManifest.from_dict(payload)


def test_canonical_hash_is_key_order_independent() -> None:
    first = calculate_payload_sha256(
        {
            "a": 1,
            "b": 2,
        }
    )
    second = calculate_payload_sha256(
        {
            "b": 2,
            "a": 1,
        }
    )

    assert first == second
