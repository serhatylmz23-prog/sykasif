from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from syk_core import GeoLocation
from syk_core.ecosystem import (
    ConservationState,
    EcosystemEntityType,
    EcosystemRuntimeContext,
    FishSpeciesProfile,
    ObservationSource,
    PlantCondition,
    PlantSpeciesProfile,
    SalinityType,
    WaterBodyType,
)
from syk_core.integration import (
    CombinedRuntimeEngine,
    CombinedRuntimeRequest,
)
from syk_core.live_analysis import (
    AnalysisFrame,
    LiveDetection,
    LiveSessionState,
)
from syk_core.live_persistence import (
    LiveAnalysisIntegrityError,
)
from syk_core.ovm import (
    BoundingRegion,
    NormalizedPoint,
    SurfaceFeature,
    SurfaceFeatureKind,
    SurfaceInput,
    SurfaceInputKind,
    SurfaceSeverity,
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
            17,
            30,
            tzinfo=UTC,
        ),
        salinity=(
            SalinityType.FRESHWATER
        ),
        water_body_type=(
            WaterBodyType.RESERVOIR
        ),
        water_body_name=(
            "Keban Baraj Gölü"
        ),
        depth_m=8.5,
        water_temperature_c=22.0,
        dissolved_oxygen_mg_l=7.6,
        ph_value=7.8,
        altitude_m=845.0,
        air_temperature_c=29.0,
        soil_moisture_percent=68.0,
        device_data_available=True,
        online_available=True,
    )


def create_frame() -> AnalysisFrame:
    return AnalysisFrame(
        source=(
            ObservationSource.LIVE_CAMERA
        ),
        location=GeoLocation(
            latitude=38.806,
            longitude=38.744,
            altitude_m=845.0,
        ),
        width_px=1920,
        height_px=1080,
        sequence_number=1,
        evidence_ids={
            "SYK-EVD-KAMERA-001",
        },
    )


def create_region(
    left: float,
    top: float,
    right: float,
    bottom: float,
) -> BoundingRegion:
    return BoundingRegion(
        top_left=NormalizedPoint(
            x=left,
            y=top,
        ),
        bottom_right=NormalizedPoint(
            x=right,
            y=bottom,
        ),
    )


def create_detections(
) -> tuple[LiveDetection, ...]:
    return (
        LiveDetection(
            entity_type="fish",
            label="Sazan",
            confidence_score=91.0,
            region=create_region(
                0.10,
                0.20,
                0.40,
                0.62,
            ),
            species_id="sazan",
            track_id="TRACK-SAZAN-001",
            evidence_ids={
                "SYK-EVD-BALIK-001",
            },
        ),
        LiveDetection(
            entity_type="plant",
            label="Söğüt",
            confidence_score=88.0,
            region=create_region(
                0.48,
                0.12,
                0.82,
                0.78,
            ),
            species_id="sogut",
            track_id="TRACK-SOGUT-001",
            condition=(
                PlantCondition.HEALTHY
            ),
            evidence_ids={
                "SYK-EVD-BİTKİ-001",
            },
        ),
    )


def create_fish_profiles(
) -> tuple[FishSpeciesProfile, ...]:
    return (
        FishSpeciesProfile(
            species_id="sazan",
            turkish_name="Sazan",
            supported_region_codes=(
                frozenset(
                    {
                        "TR-ELAZIG-KEBAN",
                    }
                )
            ),
            supported_water_body_names=(
                frozenset(
                    {
                        "keban baraj gölü",
                    }
                )
            ),
            salinity_types=frozenset(
                {
                    SalinityType.FRESHWATER,
                }
            ),
            water_body_types=frozenset(
                {
                    WaterBodyType.RESERVOIR,
                    WaterBodyType.LAKE,
                    WaterBodyType.RIVER,
                }
            ),
            minimum_depth_m=0.5,
            maximum_depth_m=30.0,
            minimum_temperature_c=4.0,
            maximum_temperature_c=30.0,
            source_pending=True,
        ),
    )


def create_plant_profiles(
) -> tuple[PlantSpeciesProfile, ...]:
    return (
        PlantSpeciesProfile(
            species_id="sogut",
            turkish_name="Söğüt",
            entity_type=(
                EcosystemEntityType.TREE
            ),
            supported_region_codes=(
                frozenset(
                    {
                        "TR-ELAZIG-KEBAN",
                    }
                )
            ),
            minimum_altitude_m=0.0,
            maximum_altitude_m=1800.0,
            minimum_soil_moisture_percent=(
                40.0
            ),
            maximum_soil_moisture_percent=(
                100.0
            ),
            water_indicator_score=92.0,
            conservation_state=(
                ConservationState.COMMON
            ),
            source_pending=True,
        ),
    )


def create_surface_inputs(
) -> tuple[SurfaceInput, ...]:
    return (
        SurfaceInput(
            input_id="SYK-DTSE-GÖRÜNTÜ-001",
            kind=SurfaceInputKind.PHOTO,
            width_px=1920,
            height_px=1080,
        ),
        SurfaceInput(
            input_id="SYK-DTSE-NOKTA-001",
            kind=(
                SurfaceInputKind.POINT_CLOUD
            ),
            point_count=1_250_000,
        ),
        SurfaceInput(
            input_id="SYK-DTSE-AĞ-001",
            kind=(
                SurfaceInputKind.ADAPTIVE_MESH
            ),
            vertex_count=275_000,
        ),
    )


def create_surface_features(
) -> tuple[SurfaceFeature, ...]:
    crack = SurfaceFeature(
        feature_id="ÇATLAK-001",
        kind=SurfaceFeatureKind.CRACK,
        title="Çatlak-01",
        description=(
            "Yüzey üzerinde ince çizgisel "
            "süreksizlik."
        ),
        region=create_region(
            0.18,
            0.32,
            0.52,
            0.72,
        ),
        confidence_score=96.1,
        severity=SurfaceSeverity.MEDIUM,
        depth_m=0.032,
        width_m=0.014,
        length_m=0.146,
        evidence_ids={
            "SYK-EVD-YÜZEY-001",
        },
    )

    cavity = SurfaceFeature(
        feature_id="OYUK-001",
        kind=SurfaceFeatureKind.CAVITY,
        title="Oyuk-01",
        description=(
            "Yüzey altında değerlendirilmesi "
            "gereken olası boşluk."
        ),
        region=create_region(
            0.56,
            0.24,
            0.84,
            0.58,
        ),
        confidence_score=58.0,
        severity=SurfaceSeverity.HIGH,
        depth_m=0.78,
        width_m=0.234,
        evidence_ids={
            "SYK-EVD-YÜZEY-002",
        },
    )

    return (
        crack,
        cavity,
    )


def create_request(
) -> CombinedRuntimeRequest:
    return CombinedRuntimeRequest(
        context=create_context(),
        frame=create_frame(),
        detections=create_detections(),
        fish_profiles=(
            create_fish_profiles()
        ),
        plant_profiles=(
            create_plant_profiles()
        ),
        surface_inputs=(
            create_surface_inputs()
        ),
        surface_features=(
            create_surface_features()
        ),
        actor="Bilge Kaan",
        cluster_distance_m=20.0,
        metadata={
            "research_point_id": (
                "SYK-RP-KEBAN-001"
            ),
            "arayüz_dili": "tr-TR",
        },
    )


def test_combined_runtime_full_chain(
    tmp_path: Path,
) -> None:
    engine = CombinedRuntimeEngine(
        repository_root=(
            tmp_path
            / "combined_repository"
        )
    )

    result = engine.execute(
        create_request()
    )

    assert result.verify() is True
    assert (
        result.summary
        .live_detection_count
        == 2
    )
    assert (
        result.summary
        .fish_match_count
        >= 1
    )
    assert (
        result.summary
        .plant_match_count
        >= 1
    )
    assert (
        result.summary
        .surface_feature_count
        == 2
    )
    assert (
        result.summary
        .annotation_count
        == 4
    )
    assert (
        result.summary
        .frame_instruction_count
        == 4
    )
    assert (
        result.summary
        .map_pin_count
        == 1
    )
    assert (
        result.summary
        .review_required
        is True
    )
    assert result.manifest.verify() is True
    assert (
        result.report_payload.verify()
        is True
    )


def test_combined_runtime_preserves_turkish(
    tmp_path: Path,
) -> None:
    engine = CombinedRuntimeEngine(
        repository_root=(
            tmp_path
            / "combined_repository"
        )
    )

    result = engine.execute(
        create_request()
    )

    payload = result.to_runtime_dict()

    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "Söğüt" in text
    assert "Çatlak-01" in text
    assert "yüzey_zekâsı" in text
    assert "inceleme_gerekli" in text
    assert "\\u00f6" not in text
    assert "\\u011f" not in text
    assert "\\u0131" not in text


def test_combined_runtime_restores_active_session_as_paused(
    tmp_path: Path,
) -> None:
    engine = CombinedRuntimeEngine(
        repository_root=(
            tmp_path
            / "combined_repository"
        )
    )

    result = engine.execute(
        create_request()
    )

    restored = engine.restore_session(
        result.session.session_id
    )

    assert (
        restored.state
        == LiveSessionState.PAUSED
    )
    assert (
        restored.processed_frame_count
        == 1
    )
    assert len(restored.history) == 2
    assert (
        restored.metadata[
            "restored_from_snapshot"
        ]
        is True
    )


def test_combined_runtime_detects_repository_tampering(
    tmp_path: Path,
) -> None:
    engine = CombinedRuntimeEngine(
        repository_root=(
            tmp_path
            / "combined_repository"
        )
    )

    result = engine.execute(
        create_request()
    )

    snapshot_path = (
        engine.repository
        .snapshot_directory
        / (
            f"{result.session.session_id}"
            ".snapshot.json"
        )
    )

    envelope = json.loads(
        snapshot_path.read_text(
            encoding="utf-8"
        )
    )

    envelope["payload"][
        "processed_frame_count"
    ] = 999

    snapshot_path.write_text(
        json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        LiveAnalysisIntegrityError
    ):
        engine.repository.verify(
            result.session.session_id
        )


def test_surface_feature_without_input_is_rejected(
    tmp_path: Path,
) -> None:
    engine = CombinedRuntimeEngine(
        repository_root=(
            tmp_path
            / "combined_repository"
        )
    )

    request = CombinedRuntimeRequest(
        context=create_context(),
        frame=create_frame(),
        detections=create_detections(),
        fish_profiles=(
            create_fish_profiles()
        ),
        plant_profiles=(
            create_plant_profiles()
        ),
        surface_inputs=tuple(),
        surface_features=(
            create_surface_features()
        ),
        actor="Bilge Kaan",
    )

    with pytest.raises(
        ValueError,
        match="en az bir yüzey girdisi",
    ):
        engine.execute(request)
