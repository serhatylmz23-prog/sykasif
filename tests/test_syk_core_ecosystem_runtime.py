from __future__ import annotations

from datetime import UTC, datetime

from syk_core import GeoLocation
from syk_core.ecosystem import (
    ConservationState,
    DynamicFishLayerEngine,
    DynamicPlantLayerEngine,
    EcosystemEntityType,
    EcosystemRuntimeContext,
    EcosystemRuntimeEngine,
    FishObservation,
    FishSpeciesProfile,
    ObservationSource,
    PlantCondition,
    PlantObservation,
    PlantSpeciesProfile,
    SalinityType,
    SonarTarget,
    WaterBodyType,
)
from syk_core.ecosystem.fish_engine import (
    create_keban_seed_profiles,
)


def create_context() -> EcosystemRuntimeContext:
    return EcosystemRuntimeContext(
        location=GeoLocation(
            latitude=38.806,
            longitude=38.744,
            altitude_m=845.0,
        ),
        region_code="TR-ELAZIG-KEBAN",
        region_name="Keban",
        observed_at=datetime(
            2026,
            8,
            4,
            14,
            30,
            tzinfo=UTC,
        ),
        salinity=SalinityType.FRESHWATER,
        water_body_type=WaterBodyType.RESERVOIR,
        water_body_name="Keban Baraj Gölü",
        depth_m=8.5,
        water_temperature_c=22.0,
        dissolved_oxygen_mg_l=7.6,
        ph_value=7.8,
        altitude_m=845.0,
        air_temperature_c=29.0,
        soil_moisture_percent=68.0,
        relative_humidity_percent=44.0,
        device_data_available=True,
    )


def test_keban_seed_profiles_are_dynamic() -> None:
    profiles = create_keban_seed_profiles()

    assert len(profiles) >= 7
    assert all(
        profile.source_pending
        for profile in profiles
    )
    assert all(
        profile.resolved_icon_code.startswith(
            "syk-fish-"
        )
        for profile in profiles
    )


def test_fish_engine_uses_context_and_sonar() -> None:
    engine = DynamicFishLayerEngine()
    profiles = create_keban_seed_profiles()

    observation = FishObservation(
        source=ObservationSource.SONAR,
        detected_label="Sazan",
        model_confidence=88.0,
        sonar_target=SonarTarget(
            target_id="SONAR-HEDEF-001",
            depth_m=8.0,
            relative_x=0.62,
            strength_percent=84.0,
            estimated_length_cm=42.0,
        ),
    )

    result = engine.evaluate(
        context=create_context(),
        species_profiles=profiles,
        observations=(observation,),
    )

    assert result.dynamic is True
    assert result.sonar_target_count == 1
    assert "sazan" in result.selected_species_ids
    assert result.matches[0].score > 60


def test_saltwater_species_is_rejected_in_keban() -> None:
    engine = DynamicFishLayerEngine()

    saltwater_species = FishSpeciesProfile(
        species_id="test_deniz_baligi",
        turkish_name="Test Deniz Balığı",
        salinity_types=frozenset(
            {
                SalinityType.SALTWATER,
            }
        ),
        water_body_types=frozenset(
            {
                WaterBodyType.SEA,
            }
        ),
        source_pending=False,
    )

    result = engine.evaluate(
        context=create_context(),
        species_profiles=(
            saltwater_species,
        ),
        minimum_match_score=45.0,
    )

    assert result.matches == tuple()


def test_plant_engine_uses_camera_and_habitat() -> None:
    engine = DynamicPlantLayerEngine()

    willow = PlantSpeciesProfile(
        species_id="sogut",
        turkish_name="Söğüt",
        entity_type=EcosystemEntityType.TREE,
        supported_region_codes=frozenset(
            {
                "TR-ELAZIG-KEBAN",
            }
        ),
        minimum_soil_moisture_percent=45.0,
        maximum_soil_moisture_percent=100.0,
        water_indicator_score=92.0,
        conservation_state=(
            ConservationState.COMMON
        ),
        source_pending=True,
    )

    observation = PlantObservation(
        source=ObservationSource.LIVE_CAMERA,
        detected_label="Söğüt",
        model_confidence=91.0,
        condition=PlantCondition.HEALTHY,
        leaf_score=88.0,
        green_coverage_percent=76.0,
    )

    result = engine.evaluate(
        context=create_context(),
        species_profiles=(willow,),
        observations=(observation,),
    )

    assert result.dynamic is True
    assert result.selected_species_ids == (
        "sogut",
    )
    assert result.water_indicator_score == 92.0
    assert result.health_summary["healthy"] == 1
    assert (
        result.matches[0].dynamic_state
        == "yüksek_olasılık"
    )


def test_ecosystem_engine_creates_common_ovm_entities() -> None:
    fish_profiles = create_keban_seed_profiles()

    plant_profile = PlantSpeciesProfile(
        species_id="kamış",
        turkish_name="Kamış",
        entity_type=(
            EcosystemEntityType.AQUATIC_PLANT
        ),
        supported_region_codes=frozenset(
            {
                "TR-ELAZIG-KEBAN",
            }
        ),
        minimum_soil_moisture_percent=50.0,
        maximum_soil_moisture_percent=100.0,
        water_indicator_score=96.0,
        source_pending=True,
    )

    engine = EcosystemRuntimeEngine()

    result = engine.analyze(
        context=create_context(),
        fish_profiles=fish_profiles,
        plant_profiles=(plant_profile,),
        fish_observations=(
            FishObservation(
                source=ObservationSource.SONAR,
                detected_label="Sazan",
                model_confidence=85.0,
                sonar_target=SonarTarget(
                    target_id="SONAR-001",
                    depth_m=6.2,
                    relative_x=0.4,
                    strength_percent=72.0,
                ),
            ),
        ),
        plant_observations=(
            PlantObservation(
                source=ObservationSource.PHOTO,
                detected_label="Kamış",
                model_confidence=90.0,
                condition=PlantCondition.HEALTHY,
            ),
        ),
    )

    assert result.dynamic is True
    assert result.entities
    assert any(
        entity.layer_code
        == "ecosystem.fish"
        for entity in result.entities
    )
    assert any(
        entity.layer_code
        == "ecosystem.plant"
        for entity in result.entities
    )
    assert result.recommendations
