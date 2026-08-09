from pathlib import Path
import hashlib
import json


ROOT = Path("terminal_v2_canonical")

CONTRACT = ROOT / "SYK_UI_CANONICAL_CONTRACT.md"
LOCK = ROOT / "SYK_UI_CANONICAL_LOCK.json"
MANIFEST = ROOT / "SYK_UI_CANONICAL_SHA256.txt"
INDEX = ROOT / "ui/index.html"
RESPONSIVE = (
    ROOT
    / "ui/css/syk_responsive_canonical_053015.css"
)


def test_contract_exists():
    assert CONTRACT.exists()


def test_lock_exists():
    assert LOCK.exists()


def test_manifest_exists():
    assert MANIFEST.exists()


def test_responsive_css_exists():
    assert RESPONSIVE.exists()


def test_single_ui_strategy():
    data = json.loads(
        LOCK.read_text(
            encoding="utf-8-sig"
        )
    )

    assert (
        data["responsive_strategy"]
        == "single_ui_pc_tablet_phone"
    )

    assert (
        data["legacy_development_allowed"]
        is False
    )


def test_visual_approval_is_required():
    data = json.loads(
        LOCK.read_text(
            encoding="utf-8-sig"
        )
    )

    assert (
        data["visual_approval_required"]
        is True
    )


def test_dynamic_matrix_required():
    data = json.loads(
        LOCK.read_text(
            encoding="utf-8-sig"
        )
    )

    assert (
        data["dynamic_right_matrix_required"]
        is True
    )


def test_world_does_not_repeat():
    data = json.loads(
        LOCK.read_text(
            encoding="utf-8-sig"
        )
    )

    assert (
        data["world_horizontal_repeat_allowed"]
        is False
    )


def test_responsive_breakpoints():
    text = RESPONSIVE.read_text(
        encoding="utf-8-sig"
    )

    assert "1101px" in text
    assert "768px" in text
    assert "600px" in text
    assert "390px" in text
    assert "pointer: coarse" in text


def test_index_loads_responsive_contract():
    text = INDEX.read_text(
        encoding="utf-8-sig"
    )

    assert (
        "syk_responsive_canonical_053015.css"
        in text
    )


def test_manifest_entries_are_valid():
    text = MANIFEST.read_text(
        encoding="utf-8-sig"
    )

    entries = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    assert len(entries) >= 4

    for entry in entries:
        sha, path = entry.split(
            None,
            1
        )

        assert len(sha) == 64

        assert all(
            c in "0123456789abcdef"
            for c in sha
        )
