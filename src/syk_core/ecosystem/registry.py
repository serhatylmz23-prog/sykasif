"""Canlı türü kayıt deposu."""

from __future__ import annotations

from .fish_engine import FishSpeciesProfile
from .plant_engine import PlantSpeciesProfile


class DuplicateSpeciesError(ValueError):
    """Tür kaydı zaten bulunuyor."""


class SpeciesNotFoundError(KeyError):
    """Tür kaydı bulunamadı."""


class EcosystemSpeciesRegistry:
    """Balık ve bitki tür profillerini birlikte yönetir."""

    def __init__(self) -> None:
        self._fish: dict[
            str,
            FishSpeciesProfile,
        ] = {}
        self._plants: dict[
            str,
            PlantSpeciesProfile,
        ] = {}

    def add_fish(
        self,
        profile: FishSpeciesProfile,
        *,
        replace: bool = False,
    ) -> None:
        species_id = profile.species_id

        if species_id in self._fish and not replace:
            raise DuplicateSpeciesError(
                f"Balık türü zaten kayıtlı: {species_id}"
            )

        self._fish[species_id] = profile

    def add_plant(
        self,
        profile: PlantSpeciesProfile,
        *,
        replace: bool = False,
    ) -> None:
        species_id = profile.species_id

        if species_id in self._plants and not replace:
            raise DuplicateSpeciesError(
                f"Bitki türü zaten kayıtlı: {species_id}"
            )

        self._plants[species_id] = profile

    def fish(
        self,
        species_id: str,
    ) -> FishSpeciesProfile:
        try:
            return self._fish[species_id]
        except KeyError as exc:
            raise SpeciesNotFoundError(
                f"Balık türü bulunamadı: {species_id}"
            ) from exc

    def plant(
        self,
        species_id: str,
    ) -> PlantSpeciesProfile:
        try:
            return self._plants[species_id]
        except KeyError as exc:
            raise SpeciesNotFoundError(
                f"Bitki türü bulunamadı: {species_id}"
            ) from exc

    def all_fish(
        self,
    ) -> tuple[FishSpeciesProfile, ...]:
        return tuple(
            sorted(
                self._fish.values(),
                key=lambda item: item.turkish_name,
            )
        )

    def all_plants(
        self,
    ) -> tuple[PlantSpeciesProfile, ...]:
        return tuple(
            sorted(
                self._plants.values(),
                key=lambda item: item.turkish_name,
            )
        )
