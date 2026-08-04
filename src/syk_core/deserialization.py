"""JSON yükleme ve çekirdek nesne yeniden oluşturma."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from .enums import (
    AccuracySource,
    EntityStatus,
    EvidenceKind,
    EvidenceStatus,
    LayerCategory,
    LayerStatus,
    ResearchCategory,
    VerificationLevel,
)
from .evidence import EvidenceRecord
from .identity import EntityIdentity
from .layer import LayerRecord
from .location import GeoLocation, ResearchArea
from .persistence_errors import SerializationError
from .research_point import ResearchPoint


def parse_datetime(
    value: str | datetime | None,
) -> datetime | None:
    """ISO-8601 zaman değerini saat dilimi bilgili UTC nesnesine çevirir."""

    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            return None

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise SerializationError(
                f"Geçersiz tarih değeri: {value}"
            ) from exc
    else:
        raise SerializationError(
            f"Desteklenmeyen tarih türü: {type(value).__name__}"
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def identity_from_dict(
    payload: dict[str, Any],
) -> EntityIdentity:
    """Sözlükten EntityIdentity oluşturur."""

    try:
        created_at = parse_datetime(payload["created_at"])
        updated_at = parse_datetime(payload["updated_at"])

        if created_at is None or updated_at is None:
            raise SerializationError(
                "Kimlik zaman alanları boş olamaz."
            )

        return EntityIdentity(
            entity_prefix=str(payload["entity_prefix"]),
            syk_id=str(payload["syk_id"]),
            uuid=UUID(str(payload["uuid"])),
            schema_version=str(payload["schema_version"]),
            created_at=created_at,
            updated_at=updated_at,
        )
    except KeyError as exc:
        raise SerializationError(
            f"Kimlik alanı eksik: {exc.args[0]}"
        ) from exc
    except ValueError as exc:
        raise SerializationError(
            f"Kimlik verisi geçersiz: {exc}"
        ) from exc


def location_from_dict(
    payload: dict[str, Any],
) -> GeoLocation:
    """Sözlükten GeoLocation oluşturur."""

    try:
        return GeoLocation(
            latitude=float(payload["latitude"]),
            longitude=float(payload["longitude"]),
            altitude_m=(
                None
                if payload.get("altitude_m") is None
                else float(payload["altitude_m"])
            ),
            horizontal_accuracy_m=(
                None
                if payload.get("horizontal_accuracy_m") is None
                else float(payload["horizontal_accuracy_m"])
            ),
            vertical_accuracy_m=(
                None
                if payload.get("vertical_accuracy_m") is None
                else float(payload["vertical_accuracy_m"])
            ),
            accuracy_source=AccuracySource(
                payload.get(
                    "accuracy_source",
                    AccuracySource.UNKNOWN.value,
                )
            ),
            coordinate_system=str(
                payload.get(
                    "coordinate_system",
                    "EPSG:4326",
                )
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SerializationError(
            f"Konum verisi geçersiz: {exc}"
        ) from exc


def area_from_dict(
    payload: dict[str, Any] | None,
) -> ResearchArea | None:
    """Sözlükten ResearchArea oluşturur."""

    if payload is None:
        return None

    try:
        center = location_from_dict(payload["center"])
        polygon_payload = payload.get("polygon") or []

        polygon = tuple(
            location_from_dict(item)
            for item in polygon_payload
        )

        return ResearchArea(
            center=center,
            radius_m=float(payload.get("radius_m", 100.0)),
            polygon=polygon,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SerializationError(
            f"Araştırma alanı verisi geçersiz: {exc}"
        ) from exc


def layer_from_dict(
    payload: dict[str, Any],
) -> LayerRecord:
    """Sözlükten LayerRecord oluşturur."""

    try:
        identity = identity_from_dict(payload["identity"])

        return LayerRecord(
            name=str(payload["name"]),
            category=LayerCategory(payload["category"]),
            identity=identity,
            status=LayerStatus(payload["status"]),
            visible=bool(payload.get("visible", False)),
            opacity=float(payload.get("opacity", 1.0)),
            priority=int(payload.get("priority", 50)),
            source=payload.get("source"),
            source_version=payload.get("source_version"),
            collected_at=parse_datetime(
                payload.get("collected_at")
            ),
            temporal_start=parse_datetime(
                payload.get("temporal_start")
            ),
            temporal_end=parse_datetime(
                payload.get("temporal_end")
            ),
            minimum_zoom=(
                None
                if payload.get("minimum_zoom") is None
                else float(payload["minimum_zoom"])
            ),
            maximum_zoom=(
                None
                if payload.get("maximum_zoom") is None
                else float(payload["maximum_zoom"])
            ),
            metadata=dict(payload.get("metadata") or {}),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SerializationError(
            f"Katman verisi geçersiz: {exc}"
        ) from exc


def evidence_from_dict(
    payload: dict[str, Any],
) -> EvidenceRecord:
    """Sözlükten EvidenceRecord oluşturur."""

    try:
        identity = identity_from_dict(payload["identity"])
        collected_at = parse_datetime(payload.get("collected_at"))

        if collected_at is None:
            raise SerializationError(
                "Kanıt collected_at alanı boş olamaz."
            )

        return EvidenceRecord(
            title=str(payload["title"]),
            kind=EvidenceKind(payload["kind"]),
            identity=identity,
            status=EvidenceStatus(payload["status"]),
            verification_level=VerificationLevel(
                payload["verification_level"]
            ),
            source_uri=payload.get("source_uri"),
            local_path=payload.get("local_path"),
            mime_type=payload.get("mime_type"),
            size_bytes=(
                None
                if payload.get("size_bytes") is None
                else int(payload["size_bytes"])
            ),
            sha256_digest=payload.get("sha256"),
            collected_at=collected_at,
            verified_at=parse_datetime(
                payload.get("verified_at")
            ),
            collector_id=payload.get("collector_id"),
            description=payload.get("description"),
            metadata=dict(payload.get("metadata") or {}),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SerializationError(
            f"Kanıt verisi geçersiz: {exc}"
        ) from exc


def research_point_from_dict(
    payload: dict[str, Any],
) -> ResearchPoint:
    """Sözlükten ResearchPoint ve bağlı kayıtlarını oluşturur."""

    try:
        point = ResearchPoint(
            title=str(payload["title"]),
            description=payload.get("description"),
            location=location_from_dict(payload["location"]),
            area=area_from_dict(payload.get("area")),
            category=ResearchCategory(payload["category"]),
            identity=identity_from_dict(payload["identity"]),
            status=EntityStatus(payload["status"]),
            priority=int(payload.get("priority", 50)),
            tags=set(payload.get("tags") or []),
            metadata=dict(payload.get("metadata") or {}),
        )

        for layer_payload in payload.get("layers") or []:
            layer = layer_from_dict(layer_payload)
            layer_id = layer.identity.syk_id or ""

            if not layer_id:
                raise SerializationError(
                    "Yüklenen katman kimliği boş."
                )

            point.layers[layer_id] = layer

        for evidence_payload in payload.get("evidence") or []:
            evidence = evidence_from_dict(evidence_payload)
            evidence_id = evidence.identity.syk_id or ""

            if not evidence_id:
                raise SerializationError(
                    "Yüklenen kanıt kimliği boş."
                )

            point.evidence[evidence_id] = evidence

        return point
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, SerializationError):
            raise

        raise SerializationError(
            f"Araştırma noktası verisi geçersiz: {exc}"
        ) from exc
