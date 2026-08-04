"""Katman kayıt deposu."""

from __future__ import annotations

from collections.abc import Iterable

from .enums import LayerCategory, LayerStatus
from .layer import LayerRecord


class LayerRepositoryError(Exception):
    """Katman deposu ana hatası."""


class DuplicateLayerError(LayerRepositoryError):
    """Aynı katman ikinci defa eklendi."""


class LayerNotFoundError(LayerRepositoryError, KeyError):
    """İstenen katman bulunamadı."""


class InMemoryLayerRepository:
    """Katman kayıtlarını bellek içinde saklar."""

    def __init__(
        self,
        records: Iterable[LayerRecord] | None = None,
    ) -> None:
        self._records: dict[str, LayerRecord] = {}

        for record in records or ():
            self.add(record)

    def add(
        self,
        record: LayerRecord,
        *,
        replace: bool = False,
    ) -> None:
        """Katman kaydı ekler."""

        layer_id = record.identity.syk_id or ""

        if not layer_id:
            raise ValueError("Katman kimliği boş olamaz.")

        if layer_id in self._records and not replace:
            raise DuplicateLayerError(
                f"Katman zaten mevcut: {layer_id}"
            )

        self._records[layer_id] = record

    def add_many(
        self,
        records: Iterable[LayerRecord],
        *,
        replace: bool = False,
    ) -> None:
        """Birden fazla katmanı ekler."""

        for record in records:
            self.add(record, replace=replace)

    def get(self, layer_id: str) -> LayerRecord:
        """Katmanı kimliğiyle döndürür."""

        try:
            return self._records[layer_id]
        except KeyError as exc:
            raise LayerNotFoundError(
                f"Katman bulunamadı: {layer_id}"
            ) from exc

    def remove(self, layer_id: str) -> LayerRecord:
        """Katmanı siler ve döndürür."""

        try:
            return self._records.pop(layer_id)
        except KeyError as exc:
            raise LayerNotFoundError(
                f"Katman bulunamadı: {layer_id}"
            ) from exc

    def find_by_category(
        self,
        category: LayerCategory,
    ) -> tuple[LayerRecord, ...]:
        """Kategoriye göre katmanları döndürür."""

        matches = [
            record
            for record in self._records.values()
            if record.category == category
        ]

        matches.sort(
            key=lambda item: (
                -item.priority,
                item.name,
            )
        )

        return tuple(matches)

    def find_by_status(
        self,
        status: LayerStatus,
    ) -> tuple[LayerRecord, ...]:
        """Duruma göre katmanları döndürür."""

        return tuple(
            sorted(
                (
                    record
                    for record in self._records.values()
                    if record.status == status
                ),
                key=lambda item: (
                    -item.priority,
                    item.name,
                ),
            )
        )

    def visible(self) -> tuple[LayerRecord, ...]:
        """Görünür katmanları döndürür."""

        return tuple(
            sorted(
                (
                    record
                    for record in self._records.values()
                    if record.visible
                ),
                key=lambda item: (
                    -item.priority,
                    item.name,
                ),
            )
        )

    def all(self) -> tuple[LayerRecord, ...]:
        """Tüm katmanları döndürür."""

        return tuple(
            sorted(
                self._records.values(),
                key=lambda item: (
                    -item.priority,
                    item.name,
                ),
            )
        )

    def clear(self) -> None:
        """Depoyu temizler."""

        self._records.clear()

    def __contains__(self, layer_id: object) -> bool:
        return layer_id in self._records

    def __len__(self) -> int:
        return len(self._records)
