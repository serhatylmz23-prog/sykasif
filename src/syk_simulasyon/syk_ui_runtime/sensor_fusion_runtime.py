from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from json import dumps
from math import asin, cos, radians, sin, sqrt
from threading import RLock
from typing import Any
from uuid import uuid4

from syk_core.sensor_gateway import (
    SensorEnvelope,
    SensorGateway,
    sensor_gateway,
)


@dataclass(frozen=True, slots=True)
class FusionRule:
    time_tolerance_seconds: float = 5.0
    location_tolerance_m: float = 15.0
    minimum_source_count: int = 2
    minimum_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.time_tolerance_seconds < 0:
            raise ValueError(
                "Zaman toleransı negatif olamaz."
            )

        if self.location_tolerance_m < 0:
            raise ValueError(
                "Konum toleransı negatif olamaz."
            )

        if self.minimum_source_count < 1:
            raise ValueError(
                "Asgari kaynak sayısı birden küçük olamaz."
            )

        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError(
                "Asgari güven değeri 0 ile 1 arasında olmalıdır."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FusionConflict:
    field: str
    values: tuple[Any, ...]
    source_ids: tuple[str, ...]
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "values": list(self.values),
            "source_ids": list(self.source_ids),
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class FusionGroup:
    group_id: str
    research_id: str | None
    workspace_id: str | None
    source_ids: tuple[str, ...]
    envelope_ids: tuple[str, ...]
    sensor_kinds: tuple[str, ...]
    created_at: str
    start_timestamp: str
    end_timestamp: str
    center_latitude: float | None
    center_longitude: float | None
    maximum_distance_m: float | None
    combined_confidence: float
    source_weights: dict[str, float]
    merged_payload: dict[str, Any]
    conflicts: tuple[FusionConflict, ...]
    evidence_group_id: str
    map_layer_packet: dict[str, Any]
    real_device_data: bool
    simulation_data: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "research_id": self.research_id,
            "workspace_id": self.workspace_id,
            "source_ids": list(self.source_ids),
            "envelope_ids": list(self.envelope_ids),
            "sensor_kinds": list(self.sensor_kinds),
            "created_at": self.created_at,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "center_latitude": self.center_latitude,
            "center_longitude": self.center_longitude,
            "maximum_distance_m": self.maximum_distance_m,
            "combined_confidence": self.combined_confidence,
            "source_weights": dict(self.source_weights),
            "merged_payload": dict(self.merged_payload),
            "conflicts": [
                conflict.to_dict()
                for conflict in self.conflicts
            ],
            "conflict_count": len(self.conflicts),
            "evidence_group_id": self.evidence_group_id,
            "map_layer_packet": dict(
                self.map_layer_packet
            ),
            "real_device_data": self.real_device_data,
            "simulation_data": self.simulation_data,
        }


class SensorFusionRuntime:
    def __init__(
        self,
        *,
        gateway: SensorGateway,
    ) -> None:
        self._gateway = gateway
        self._lock = RLock()

        self._groups: dict[
            str,
            FusionGroup,
        ] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(
            UTC
        ).isoformat()

    def reset(self) -> None:
        with self._lock:
            self._groups.clear()

    def get(
        self,
        group_id: str,
    ) -> FusionGroup | None:
        with self._lock:
            return self._groups.get(
                group_id
            )

    def list(
        self,
        *,
        research_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[FusionGroup]:
        with self._lock:
            groups = list(
                self._groups.values()
            )

        if research_id is not None:
            groups = [
                group
                for group in groups
                if group.research_id == research_id
            ]

        if workspace_id is not None:
            groups = [
                group
                for group in groups
                if group.workspace_id == workspace_id
            ]

        return sorted(
            groups,
            key=lambda item: item.created_at,
        )

    def fuse(
        self,
        *,
        research_id: str | None,
        workspace_id: str | None,
        rule: FusionRule,
        source_weights: dict[str, float] | None = None,
    ) -> list[FusionGroup]:
        envelopes = list(
            self._gateway.list_envelopes(
                research_id=research_id,
                workspace_id=workspace_id,
            )
        )

        envelopes = [
            envelope
            for envelope in envelopes
            if envelope.confidence
            >= rule.minimum_confidence
        ]

        envelopes.sort(
            key=lambda item: (
                item.timestamp,
                item.source_id,
                item.sequence,
            )
        )

        clusters = self._cluster(
            envelopes,
            rule=rule,
        )

        created: list[FusionGroup] = []

        for cluster in clusters:
            source_ids = {
                envelope.source_id
                for envelope in cluster
            }

            if (
                len(source_ids)
                < rule.minimum_source_count
            ):
                continue

            group = self._build_group(
                cluster,
                research_id=research_id,
                workspace_id=workspace_id,
                source_weights=source_weights or {},
            )

            with self._lock:
                self._groups[
                    group.group_id
                ] = group

            created.append(group)

        return created

    def _cluster(
        self,
        envelopes: list[SensorEnvelope],
        *,
        rule: FusionRule,
    ) -> list[list[SensorEnvelope]]:
        clusters: list[
            list[SensorEnvelope]
        ] = []

        for envelope in envelopes:
            placed = False

            for cluster in clusters:
                if self._matches_cluster(
                    envelope,
                    cluster,
                    rule=rule,
                ):
                    cluster.append(envelope)
                    placed = True
                    break

            if not placed:
                clusters.append(
                    [envelope]
                )

        return clusters

    def _matches_cluster(
        self,
        envelope: SensorEnvelope,
        cluster: list[SensorEnvelope],
        *,
        rule: FusionRule,
    ) -> bool:
        reference = cluster[0]

        time_delta = abs(
            (
                self._parse_time(
                    envelope.timestamp
                )
                - self._parse_time(
                    reference.timestamp
                )
            ).total_seconds()
        )

        if (
            time_delta
            > rule.time_tolerance_seconds
        ):
            return False

        envelope_position = self._position(
            envelope
        )

        cluster_positions = [
            position
            for item in cluster
            if (
                position := self._position(
                    item
                )
            )
            is not None
        ]

        if (
            envelope_position is None
            or not cluster_positions
        ):
            return True

        center = self._center(
            cluster_positions
        )

        distance = self._distance_m(
            envelope_position[0],
            envelope_position[1],
            center[0],
            center[1],
        )

        return (
            distance
            <= rule.location_tolerance_m
        )

    def _build_group(
        self,
        envelopes: list[SensorEnvelope],
        *,
        research_id: str | None,
        workspace_id: str | None,
        source_weights: dict[str, float],
    ) -> FusionGroup:
        normalized_weights = (
            self._normalized_weights(
                envelopes,
                source_weights,
            )
        )

        combined_confidence = (
            self._combined_confidence(
                envelopes,
                normalized_weights,
            )
        )

        positions = [
            position
            for envelope in envelopes
            if (
                position := self._position(
                    envelope
                )
            )
            is not None
        ]

        center_latitude: float | None = None
        center_longitude: float | None = None
        maximum_distance_m: float | None = None

        if positions:
            center_latitude, center_longitude = (
                self._center(
                    positions
                )
            )

            maximum_distance_m = round(
                max(
                    self._distance_m(
                        latitude,
                        longitude,
                        center_latitude,
                        center_longitude,
                    )
                    for latitude, longitude
                    in positions
                ),
                3,
            )

        merged_payload, conflicts = (
            self._merge_payloads(
                envelopes
            )
        )

        source_ids = tuple(
            sorted(
                {
                    envelope.source_id
                    for envelope in envelopes
                }
            )
        )

        envelope_ids = tuple(
            envelope.envelope_id
            for envelope in envelopes
        )

        sensor_kinds = tuple(
            sorted(
                {
                    envelope.kind.value
                    for envelope in envelopes
                }
            )
        )

        timestamps = [
            envelope.timestamp
            for envelope in envelopes
        ]

        real_device_data = all(
            envelope.real_device_data
            for envelope in envelopes
        )

        simulation_data = all(
            envelope.simulation_data
            for envelope in envelopes
        )

        if (
            real_device_data
            and simulation_data
        ):
            raise RuntimeError(
                "Birleşik grupta gerçek ve simülasyon "
                "verisi aynı anda etkin olamaz."
            )

        digest_payload = dumps(
            {
                "envelope_ids": envelope_ids,
                "research_id": research_id,
                "workspace_id": workspace_id,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = sha256(
            digest_payload.encode("utf-8")
        ).hexdigest()

        group_id = str(uuid4())

        evidence_group_id = (
            "evidence-group-"
            + digest[:32]
        )

        map_layer_packet = {
            "layer_key": "sensor-fusion",
            "group_id": group_id,
            "workspace_id": workspace_id,
            "position": (
                {
                    "latitude": center_latitude,
                    "longitude": center_longitude,
                }
                if (
                    center_latitude is not None
                    and center_longitude is not None
                )
                else None
            ),
            "sensor_kinds": list(
                sensor_kinds
            ),
            "source_count": len(
                source_ids
            ),
            "combined_confidence": (
                combined_confidence
            ),
            "conflict_count": len(
                conflicts
            ),
            "evidence_group_id": (
                evidence_group_id
            ),
        }

        return FusionGroup(
            group_id=group_id,
            research_id=research_id,
            workspace_id=workspace_id,
            source_ids=source_ids,
            envelope_ids=envelope_ids,
            sensor_kinds=sensor_kinds,
            created_at=self._now(),
            start_timestamp=min(timestamps),
            end_timestamp=max(timestamps),
            center_latitude=center_latitude,
            center_longitude=center_longitude,
            maximum_distance_m=maximum_distance_m,
            combined_confidence=combined_confidence,
            source_weights=normalized_weights,
            merged_payload=merged_payload,
            conflicts=tuple(conflicts),
            evidence_group_id=evidence_group_id,
            map_layer_packet=map_layer_packet,
            real_device_data=real_device_data,
            simulation_data=simulation_data,
        )

    @staticmethod
    def _normalized_weights(
        envelopes: list[SensorEnvelope],
        supplied: dict[str, float],
    ) -> dict[str, float]:
        source_ids = sorted(
            {
                envelope.source_id
                for envelope in envelopes
            }
        )

        raw: dict[str, float] = {}

        for source_id in source_ids:
            weight = float(
                supplied.get(
                    source_id,
                    1.0,
                )
            )

            if weight <= 0:
                raise ValueError(
                    "Kaynak ağırlığı sıfırdan büyük olmalıdır."
                )

            raw[source_id] = weight

        total = sum(
            raw.values()
        )

        return {
            source_id: round(
                weight / total,
                6,
            )
            for source_id, weight
            in raw.items()
        }

    @staticmethod
    def _combined_confidence(
        envelopes: list[SensorEnvelope],
        weights: dict[str, float],
    ) -> float:
        source_confidences: dict[
            str,
            list[float],
        ] = {}

        for envelope in envelopes:
            source_confidences.setdefault(
                envelope.source_id,
                [],
            ).append(
                envelope.confidence
            )

        result = 0.0

        for source_id, values in (
            source_confidences.items()
        ):
            source_average = (
                sum(values)
                / len(values)
            )

            result += (
                source_average
                * weights[source_id]
            )

        return round(
            max(
                0.0,
                min(
                    1.0,
                    result,
                ),
            ),
            4,
        )

    @staticmethod
    def _merge_payloads(
        envelopes: list[SensorEnvelope],
    ) -> tuple[
        dict[str, Any],
        list[FusionConflict],
    ]:
        field_values: dict[
            str,
            list[
                tuple[
                    str,
                    Any,
                ]
            ],
        ] = {}

        for envelope in envelopes:
            for field, value in (
                envelope.payload.items()
            ):
                if field == "gps":
                    continue

                field_values.setdefault(
                    field,
                    [],
                ).append(
                    (
                        envelope.source_id,
                        value,
                    )
                )

        merged: dict[str, Any] = {}
        conflicts: list[
            FusionConflict
        ] = []

        for field, items in (
            field_values.items()
        ):
            values = [
                value
                for _, value in items
            ]

            unique_serialized = {
                dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                )
                for value in values
            }

            numeric_values = [
                float(value)
                for value in values
                if (
                    isinstance(
                        value,
                        (
                            int,
                            float,
                        ),
                    )
                    and not isinstance(
                        value,
                        bool,
                    )
                )
            ]

            if (
                numeric_values
                and len(numeric_values)
                == len(values)
            ):
                merged[field] = round(
                    sum(numeric_values)
                    / len(numeric_values),
                    6,
                )

                spread = (
                    max(numeric_values)
                    - min(numeric_values)
                )

                tolerance = max(
                    abs(
                        merged[field]
                    )
                    * 0.05,
                    0.01,
                )

                if spread > tolerance:
                    conflicts.append(
                        FusionConflict(
                            field=field,
                            values=tuple(values),
                            source_ids=tuple(
                                source_id
                                for source_id, _
                                in items
                            ),
                            severity="warning",
                        )
                    )

                continue

            merged[field] = values[-1]

            if len(unique_serialized) > 1:
                conflicts.append(
                    FusionConflict(
                        field=field,
                        values=tuple(values),
                        source_ids=tuple(
                            source_id
                            for source_id, _
                            in items
                        ),
                        severity="warning",
                    )
                )

        return merged, conflicts

    @staticmethod
    def _position(
        envelope: SensorEnvelope,
    ) -> tuple[
        float,
        float,
    ] | None:
        payload = envelope.payload

        latitude = payload.get(
            "latitude"
        )

        longitude = payload.get(
            "longitude"
        )

        gps = payload.get("gps")

        if isinstance(gps, dict):
            latitude = gps.get(
                "latitude",
                latitude,
            )

            longitude = gps.get(
                "longitude",
                longitude,
            )

        try:
            if (
                latitude is None
                or longitude is None
            ):
                return None

            return (
                float(latitude),
                float(longitude),
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _center(
        positions: list[
            tuple[
                float,
                float,
            ]
        ],
    ) -> tuple[
        float,
        float,
    ]:
        return (
            sum(
                latitude
                for latitude, _
                in positions
            )
            / len(positions),
            sum(
                longitude
                for _, longitude
                in positions
            )
            / len(positions),
        )

    @staticmethod
    def _distance_m(
        latitude_1: float,
        longitude_1: float,
        latitude_2: float,
        longitude_2: float,
    ) -> float:
        earth_radius_m = 6371000.0

        latitude_delta = radians(
            latitude_2 - latitude_1
        )

        longitude_delta = radians(
            longitude_2 - longitude_1
        )

        first_latitude = radians(
            latitude_1
        )

        second_latitude = radians(
            latitude_2
        )

        value = (
            sin(latitude_delta / 2) ** 2
            + cos(first_latitude)
            * cos(second_latitude)
            * sin(longitude_delta / 2) ** 2
        )

        return (
            2
            * earth_radius_m
            * asin(
                sqrt(value)
            )
        )

    @staticmethod
    def _parse_time(
        value: str,
    ) -> datetime:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )


sensor_fusion_runtime = SensorFusionRuntime(
    gateway=sensor_gateway
)