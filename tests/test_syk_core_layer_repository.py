from __future__ import annotations

import pytest

from syk_core import (
    DuplicateLayerError,
    InMemoryLayerRepository,
    LayerCatalog,
    LayerCategory,
    LayerDefinition,
    LayerNotFoundError,
    LayerRecord,
    ResearchCategory,
)


def test_default_catalog_contains_core_layers() -> None:
    catalog = LayerCatalog.create_default()

    assert len(catalog) >= 25
    assert catalog.get("base_map").category == LayerCategory.BASE_MAP
    assert catalog.get("geology").category == LayerCategory.GEOLOGY
    assert catalog.get("evidence").category == LayerCategory.EVIDENCE


def test_catalog_filters_research_category() -> None:
    catalog = LayerCatalog.create_default()

    compatible = catalog.compatible_with(
        ResearchCategory.ARCHAEOLOGY
    )
    codes = {
        definition.code
        for definition in compatible
    }

    assert "archaeology" in codes
    assert "history" in codes
    assert "temporal" in codes
    assert "base_map" in codes


def test_catalog_rejects_duplicate_code() -> None:
    definition = LayerDefinition(
        code="test_layer",
        name="Test Katmanı",
        category=LayerCategory.CUSTOM,
        default_priority=50,
        default_opacity=0.5,
        compatible_research_categories=frozenset(
            {
                ResearchCategory.GENERAL,
            }
        ),
    )

    catalog = LayerCatalog([definition])

    with pytest.raises(ValueError):
        catalog.register(definition)


def test_repository_add_get_remove() -> None:
    repository = InMemoryLayerRepository()
    layer = LayerRecord(
        name="Topografya",
        category=LayerCategory.TOPOGRAPHY,
    )

    layer_id = layer.identity.syk_id or ""

    repository.add(layer)

    assert len(repository) == 1
    assert repository.get(layer_id) is layer
    assert layer_id in repository

    removed = repository.remove(layer_id)

    assert removed is layer
    assert len(repository) == 0


def test_repository_rejects_duplicate() -> None:
    repository = InMemoryLayerRepository()
    layer = LayerRecord(
        name="Jeoloji",
        category=LayerCategory.GEOLOGY,
    )

    repository.add(layer)

    with pytest.raises(DuplicateLayerError):
        repository.add(layer)


def test_repository_reports_missing_layer() -> None:
    repository = InMemoryLayerRepository()

    with pytest.raises(LayerNotFoundError):
        repository.get("SYK-LYR-YOK")


def test_repository_filters_visible_layers() -> None:
    repository = InMemoryLayerRepository()

    visible = LayerRecord(
        name="GPS",
        category=LayerCategory.GPS,
        visible=True,
        priority=100,
    )
    hidden = LayerRecord(
        name="Jeoloji",
        category=LayerCategory.GEOLOGY,
        visible=False,
        priority=90,
    )

    repository.add_many(
        [
            visible,
            hidden,
        ]
    )

    result = repository.visible()

    assert len(result) == 1
    assert result[0] is visible
