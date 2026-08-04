"""OVM varlık kayıt deposu."""

from __future__ import annotations

from collections.abc import Iterable

from .entity import OvmEntity
from .enums import EntityKind


class OvmRegistryError(Exception):
    """OVM depo hatası."""


class DuplicateEntityError(OvmRegistryError):
    """Aynı OVM varlığı tekrar eklendi."""


class EntityNotFoundError(OvmRegistryError, KeyError):
    """OVM varlığı bulunamadı."""


class OvmEntityRegistry:
    """Tüm modüllerin ortak varlık deposu."""

    def __init__(
        self,
        entities: Iterable[OvmEntity] | None = None,
    ) -> None:
        self._entities: dict[str, OvmEntity] = {}

        for entity in entities or ():
            self.add(entity)

    def add(
        self,
        entity: OvmEntity,
        *,
        replace: bool = False,
    ) -> None:
        entity_id = entity.entity_id

        if entity_id in self._entities and not replace:
            raise DuplicateEntityError(
                f"Varlık zaten kayıtlı: {entity_id}"
            )

        self._entities[entity_id] = entity

    def get(
        self,
        entity_id: str,
    ) -> OvmEntity:
        try:
            return self._entities[entity_id]
        except KeyError as exc:
            raise EntityNotFoundError(
                f"Varlık bulunamadı: {entity_id}"
            ) from exc

    def remove(
        self,
        entity_id: str,
    ) -> OvmEntity:
        try:
            return self._entities.pop(entity_id)
        except KeyError as exc:
            raise EntityNotFoundError(
                f"Varlık bulunamadı: {entity_id}"
            ) from exc

    def by_kind(
        self,
        kind: EntityKind,
    ) -> tuple[OvmEntity, ...]:
        return tuple(
            sorted(
                (
                    entity
                    for entity in self._entities.values()
                    if entity.kind == kind
                ),
                key=lambda item: (
                    item.layer_order,
                    item.title,
                ),
            )
        )

    def visible(self) -> tuple[OvmEntity, ...]:
        return tuple(
            sorted(
                (
                    entity
                    for entity in self._entities.values()
                    if entity.visible
                ),
                key=lambda item: (
                    item.layer_order,
                    item.title,
                ),
            )
        )

    def children_of(
        self,
        parent_id: str,
    ) -> tuple[OvmEntity, ...]:
        return tuple(
            entity
            for entity in self._entities.values()
            if entity.parent_id == parent_id
        )

    def all(self) -> tuple[OvmEntity, ...]:
        return tuple(
            sorted(
                self._entities.values(),
                key=lambda item: (
                    item.layer_order,
                    item.title,
                ),
            )
        )

    def __len__(self) -> int:
        return len(self._entities)

    def __contains__(
        self,
        entity_id: object,
    ) -> bool:
        return entity_id in self._entities
