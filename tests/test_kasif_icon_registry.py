from pathlib import Path

from syk_simulasyon.syk_ui_runtime.kasif_icon_registry import (
    KasifIconRegistry,
)


def test_ikon_manifesti_yuklenir():
    registry = KasifIconRegistry()

    snapshot = registry.snapshot()

    assert snapshot[
        "icon_count"
    ] == 27

    assert len(
        snapshot[
            "manifest_sha256"
        ]
    ) == 64


def test_kasif_gorsel_kurallari():
    registry = KasifIconRegistry()

    kasif = registry.get(
        "kasif"
    )

    rules = kasif[
        "visual_rules"
    ]

    assert (
        rules["hooded"]
        is True
    )

    assert (
        rules["face_visible"]
        is False
    )

    assert (
        rules["eyes_visible"]
        is False
    )

    assert (
        rules["headphones"]
        is False
    )

    assert (
        rules["mysterious"]
        is True
    )


def test_ikonlar_siralanir():
    registry = KasifIconRegistry()

    icons = registry.list()

    orders = [
        icon["order"]
        for icon in icons
    ]

    assert orders == sorted(
        orders
    )

    assert (
        icons[0]["icon_id"]
        == "map"
    )


def test_ikon_aramasi_turkce():
    registry = KasifIconRegistry()

    result = registry.search(
        "yer altı"
    )

    ids = {
        icon["icon_id"]
        for icon in result
    }

    assert "gpr" in ids
    assert "ert" in ids


def test_grup_filtreleme():
    registry = KasifIconRegistry()

    result = registry.list(
        group="geophysics"
    )

    ids = {
        icon["icon_id"]
        for icon in result
    }

    assert {
        "magnetometer",
        "gravimeter",
        "gpr",
        "seismic",
        "ert",
    }.issubset(ids)


def test_asistan_adi_kasif():
    registry = KasifIconRegistry()

    profile = (
        registry.assistant_profile()
    )

    assert (
        profile["display_name"]
        == "Kaşif"
    )

    assert (
        profile["role"]
        == "Bilge Asistan"
    )