from __future__ import annotations

from typing import Any, Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from pydantic import BaseModel, Field

from syk_core.sensor_gateway import (
    SensorAuthority,
    SensorHealth,
    SensorKind,
)

from .sensor_gateway_runtime import (
    sensor_gateway_runtime,
)


class SensorSourceRequest(BaseModel):
    source_id: str = Field(
        min_length=1,
        max_length=180,
    )
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    kind: SensorKind
    authority: SensorAuthority
    health: SensorHealth = (
        SensorHealth.HEALTHY
    )
    real_device_data: bool
    simulation_data: bool
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class SensorIngestRequest(BaseModel):
    payload: dict[str, Any]
    research_id: str | None = Field(
        default=None,
        max_length=180,
    )
    workspace_id: str | None = Field(
        default=None,
        max_length=180,
    )
    evidence_status: str = Field(
        default="candidate-unverified",
        min_length=1,
        max_length=120,
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


sensor_gateway_router = APIRouter(
    prefix="/api/syk-ui/sensor-gateway",
    tags=["syk-ui-sensor-gateway"],
)


@sensor_gateway_router.get("")
def gateway_snapshot() -> dict[str, object]:
    return sensor_gateway_runtime.snapshot()


@sensor_gateway_router.post(
    "/sources",
    status_code=201,
)
def register_source(
    request: SensorSourceRequest,
) -> dict[str, object]:
    try:
        source = (
            sensor_gateway_runtime.register_source(
                source_id=request.source_id,
                name=request.name,
                kind=request.kind,
                authority=request.authority,
                health=request.health,
                real_device_data=(
                    request.real_device_data
                ),
                simulation_data=(
                    request.simulation_data
                ),
                metadata=request.metadata,
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return source.to_dict()


@sensor_gateway_router.post(
    "/sources/{source_id}/ingest",
    status_code=201,
)
def ingest(
    source_id: str,
    request: SensorIngestRequest,
) -> dict[str, object]:
    try:
        envelope = sensor_gateway_runtime.ingest(
            source_id,
            payload=request.payload,
            research_id=request.research_id,
            workspace_id=request.workspace_id,
            evidence_status=request.evidence_status,
            confidence=request.confidence,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return envelope.to_dict()


@sensor_gateway_router.get(
    "/envelopes"
)
def list_envelopes(
    source_id: Annotated[
        str | None,
        Query(),
    ] = None,
    research_id: Annotated[
        str | None,
        Query(),
    ] = None,
    workspace_id: Annotated[
        str | None,
        Query(),
    ] = None,
) -> dict[str, object]:
    envelopes = (
        sensor_gateway_runtime.list_envelopes(
            source_id=source_id,
            research_id=research_id,
            workspace_id=workspace_id,
        )
    )

    return {
        "count": len(envelopes),
        "envelopes": envelopes,
    }